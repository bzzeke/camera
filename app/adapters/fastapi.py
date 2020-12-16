import re
import aiofiles
import stat
import os

from email.utils import formatdate
from starlette.responses import FileResponse
from starlette.requests import Scope, Receive, Send

class MediaResponse(FileResponse):
    def __init__(self, *args, **kwargs):
        self.chunk_size = 512 * 512
        self.request_headers = kwargs.pop('request_headers')
        super(MediaResponse, self).__init__(*args, **kwargs)

    def parse_byte_range(self, byte_range):

        if byte_range.strip() == "":
            return None, None

        m = re.compile(r"bytes=(\d+)-(\d+)?$").match(byte_range)
        if not m:
            return None, None

        start, stop = [x and int(x) for x in m.groups()]
        if stop and stop < start:
            return None, None

        return start, stop

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.stat_result is None:
            try:
                stat_result = await aiofiles.os.stat(self.path)
                self.set_stat_headers(stat_result)
            except FileNotFoundError:
                raise RuntimeError(f"File at path {self.path} does not exist.")
            else:
                mode = stat_result.st_mode
                if not stat.S_ISREG(mode):
                    raise RuntimeError(f"File at path {self.path} is not a file.")

        start = 0
        stop = None
        response_length = 0
        if 'Range' in self.request_headers:
            start, stop = self.parse_byte_range(self.request_headers['Range'])
            fs = os.stat(self.path)
            file_len = fs[6]
            if stop is None or stop >= file_len:
                stop = file_len - 1
            response_length = stop - start + 1

            self.headers["Accept-Ranges"] = "bytes"
            self.headers["Content-Range"] = "bytes {}-{}/{}".format(start, stop, file_len)
            self.headers["Content-Length"] = str(response_length)
            self.headers["Last-Modified"] = formatdate(fs.st_mtime, usegmt=True)

        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        if self.send_header_only:
            await send({"type": "http.response.body", "body": b"", "more_body": False})
        else:

            async with aiofiles.threadpool.open(self.path, mode='rb') as file:
                await file.seek(start)

                more_body = True
                while more_body:
                    pos = await file.tell()
                    to_read = min(self.chunk_size, stop + 1 - pos if stop else self.chunk_size)
                    chunk = await file.read(to_read)
                    more_body = len(chunk) == to_read and to_read > 0

                    await send(
                        {
                            "type": "http.response.body",
                            "body": chunk,
                            "more_body": more_body,
                        }
                    )
        if self.background is not None:
            await self.background()