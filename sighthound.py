from xml.etree import ElementTree
import http.client
import time
import ssl
from base64 import b64encode
import random

class Sighthound():
    rpc_path = "/xmlrpc/"
    user = ""
    password = ""
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.conn = http.client.HTTPSConnection(self.host, context=ssl._create_unverified_context())

    def send_request(self, bmsg):

        digest = b64encode(bytes("%s:%s" % (self.user, self.password), "utf-8")).decode("ascii")
        headers = {
            "Authorization": "Basic %s" % digest,
            "Content-Type": "application/xml"
        }

        self.conn.request("POST", self.rpc_path, body=bmsg, headers=headers)
        resp = self.conn.getresponse().read()

        return resp

    def getClips(self, camera = "", rule = "", date = None, limit = 500):

        if (camera == ""):
            camera = "Any camera"

        if (rule == ""):
            rule = "All objects"

        if (date == None):
            date = time.time()

        xml = '''<?xml version="1.0"?>
            <methodCall>
                <methodName>remoteGetClipsForRule</methodName>
                <params>
                    <param>
                        <value>
                            <string>%s</string>
                        </value>
                    </param>
                    <param>
                        <value>
                            <string>%s</string>
                        </value>
                    </param>
                    <param>
                        <value>
                            <int>%d</int>
                        </value>
                    </param>
                    <param>
                        <value>
                            <int>%d</int>
                        </value>
                    </param>
                    <param>
                        <value>
                            <int>0</int>
                        </value>
                    </param>
                    <param>
                        <value>
                            <boolean>0</boolean>
                        </value>
                    </param>
                </params>
            </methodCall>''' % (camera, rule, date, limit)

        response = self.send_request(xml)

        dom = ElementTree.fromstring(response)
        clips = dom.findall(
            './params/param/value/array/data/value/array/data/value'
        )

        result = {}
        for clip in clips:
            result[str(clip[0][0][1][0][0][0][0].text)] = {
                'camera':  clip[0][0][0][0].text,
                'first_id': int(clip[0][0][1][0][0][1][0].text),
                'first_timestamp': int(clip[0][0][1][0][0][0][0].text),
                'second_timestamp': int(clip[0][0][2][0][0][0][0].text),
                'second_id': int(clip[0][0][2][0][0][1][0].text),
                'third_timestamp': int(clip[0][0][3][0][0][0][0].text),
                'third_id': int(clip[0][0][3][0][0][1][0].text),
                'object_ids': int(clip[0][0][5][0][0][0][0].text) if len(clip[0][0]) > 5 else 0
            }

        return result

    def getClipUrl(self, command, clip):
        xml = '''<?xml version="1.0"?>
            <methodCall>
                <methodName>remoteGetClipUri</methodName>
                <params>
                    <param>
                        <value>
                            <string>%s</string>
                        </value>
                    </param>
                    <param>
                        <value>
                            <array>
                                <data>
                                    <value>
                                        <int>%d</int>
                                    </value>
                                    <value>
                                        <int>%d</int>
                                    </value>
                                </data>
                            </array>
                        </value>
                    </param>
                    <param>
                        <value>
                            <array>
                                <data>
                                    <value>
                                        <int>%d</int>
                                    </value>
                                    <value>
                                        <int>%d</int>
                                    </value>
                                </data>
                            </array>
                        </value>
                    </param>
                    <param>
                        <value>
                            <int>%d</int>
                        </value>
                    </param>
                    <param>
                        <value>
                            <string>video/h264</string>
                        </value>
                    </param>
                    <param>
                        <value>
                            <struct>
                                <member>
                                    <name>objectIds</name>
                                    <value>
                                        <array>
                                            <data>
                                                <value>
                                                    <int>%d</int>
                                                </value>
                                            </data>
                                        </array>
                                    </value>
                                </member>
                            </struct>
                        </value>
                    </param>
                </params>
            </methodCall>''' % (
                clip["camera"],
                clip["first_timestamp"],
                clip["first_id"],
                clip["second_timestamp"],
                clip["second_id"],
                random.randrange(1, 999, 1),
                clip["object_ids"]
                )

        response = self.send_request(xml)
        dom = ElementTree.fromstring(response)

        return dom[0][0][0][0][0][1][0].text

    def getVideoUrl(self, clip, type = None):

        command = "remoteGetClipUriForDownload" if type == "download" else "remoteGetClipUri"
        url = "https://%s:%s@%s%s?%s%s" % (
            self.user,
            self.password,
            self.host,
            self.getClipUrl(command, clip),
            clip["camera"],
            clip["first_timestamp"]
            )

        return url


    def getThumbnailUrl(self, clip):
        sizex = 1920
        sizey = 1080

        xml = '''<?xml version="1.0"?>
            <methodCall>
                <methodName>remoteGetThumbnailUris</methodName>
                <params>
                    <param>
                        <value>
                            <array>
                                <data>
                                    <value>
                                        <array>
                                            <data>
                                                <value>
                                                    <string>%s</string>
                                                </value>
                                                <value>
                                                    <array>
                                                        <data>
                                                            <value>
                                                                <int>%d</int>
                                                            </value>
                                                            <value>
                                                                <int>%d</int>
                                                            </value>
                                                        </data>
                                                    </array>
                                                </value>
                                            </data>
                                        </array>
                                    </value>
                                </data>
                            </array>
                        </value>
                    </param>
                    <param>
                        <value>
                            <string>image/jpeg</string>
                        </value>
                    </param>
                    <param>
                        <value>
                            <struct>
                                <member>
                                    <name>maxSize</name>
                                    <value>
                                        <array>
                                            <data>
                                                <value>
                                                    <int>%d</int>
                                                </value>
                                                <value>
                                                    <int>%d</int>
                                                </value>
                                            </data>
                                        </array>
                                    </value>
                                </member>
                            </struct>
                        </value>
                    </param>
                </params>
            </methodCall>''' % (
                clip["camera"],
                clip["first_timestamp"],
                clip["first_id"],
                sizex,
                sizey
                )

        response = self.send_request(xml)
        dom = ElementTree.fromstring(response)

        url = "https://%s:%s@%s%s" % (
            self.user,
            self.password,
            self.host,
            dom[0][0][0][0][0][1][0][0][0][0].text
            )
        return url
