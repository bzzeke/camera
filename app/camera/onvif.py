## -*- coding: utf-8 -*-
## Onvif camera controlling class that uses soap
## Pekka Jäppinen 2014
## Conversion to Python3 Petri Savolainen 2017

import datetime
import base64
import string
import base64
import requests

from hashlib import sha1
from random import SystemRandom

class Onvif():

    namespaces = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "schema": "http://www.onvif.org/ver10/schema",
        "media": "http://www.onvif.org/ver10/media/wsdl",
        "ptz": "http://www.onvif.org/ver20/ptz/wsdl"
    }

    onvif_url = ""

    def __init__(self, host, cpath="/onvif/device_service"):
        self.onvif_url = "http://{}{}".format(host, cpath)

    def set_auth(self, username, password):
        self.username = username
        self.password = password

    # SOAP handling utility functions

    def insert_in_invelope(self, msg):
        return '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">{}</s:Envelope>'.format(msg)

    def insert_in_body(self, msg):
        return '<s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">{}</s:Body>'.format(msg)

    def sendSoapMsg(self, bmsg):
        fullmsg = '{}{}'.format(self.create_auth_header(), self.insert_in_body(bmsg))
        soapmsg = self.insert_in_invelope(fullmsg)

        response = requests.post(self.onvif_url, soapmsg)
        return response.text

    def create_auth_header(self):
        created = datetime.datetime.now().isoformat().split(".")[0]
        pool = string.ascii_letters + string.digits + string.punctuation
        n64 = ''.join(SystemRandom().choice(pool) for _ in range(22))
        nonce = base64.b64encode(n64.encode('ascii')).decode("ascii")
        base = (n64 + created + self.password).encode("ascii")
        pdigest = base64.b64encode(sha1(base).digest()).decode("ascii")
        username = '<Username>{}</Username>'.format(self.username)
        password= '<Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{}</Password>'.format(pdigest)
        Nonce = '<Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{}</Nonce>'.format(nonce)
        created = '<Created xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">{}</Created>'.format(created)
        usertoken= '<UsernameToken>{}{}{}{}</UsernameToken>'.format(username, password, Nonce, created)
        header = '<s:Header><Security s:mustUnderstand="1" xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">{}</Security></s:Header>'.format(usertoken)
        return header

    def create_profile_token(self, profile_token):
        return '<ProfileToken>{}</ProfileToken>'.format(profile_token)

    # Onvif messages

    def getSystemDateAndTime(self):
        bmsg = '<GetSystemDateAndTime xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
        return self.sendSoapMsg(bmsg)

    def getCapabilities(self):
        bmsg = '<GetCapabilities xmlns="http://www.onvif.org/ver10/device/wsdl"><Category>All</Category></GetCapabilities>'
        return self.sendSoapMsg(bmsg)

    def getServiceCapabilities(self):
        bmsg = '<GetServiceCapabilities xmlns="http://www.onvif.org/ver10/device/wsdl"></GetServiceCapabilities>'
        return self.sendSoapMsg(bmsg)

    def getServices(self):
        bmsg='<GetServices xmlns="http://www.onvif.org/ver10/device/wsdl"><IncludeCapability>false</IncludeCapability></GetServices>'
        return self.sendSoapMsg(bmsg)

    def getProfiles(self):
        bmsg='<GetProfiles xmlns="http://www.onvif.org/ver10/media/wsdl"/>'
        return self.sendSoapMsg(bmsg)

    def getDeviceInformation(self):
        bmsg='<GetDeviceInformation xmlns="http://www.onvif.org/ver10/device/wsdl"/>'
        return self.sendSoapMsg(bmsg)

    def getNode(self, node_token):
        bmsg='<GetNode xmlns="http://www.onvif.org/ver20/ptz/wsdl"><NodeToken>{}</NodeToken></GetNode>'.format(node_token)
        return self.sendSoapMsg(bmsg)

    # PTZ

    def relativeMove(self, profile_token, x, y, xspeed="0.5", yspeed="0.5"):
        pantilt = '<PanTilt x="{}" y="{}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(x, y)
        pantilts ='<PanTilt x="{}" y="{}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(xspeed, yspeed)
        bmsg='<RelativeMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}<Translation>{}</Translation><Speed>{}</Speed></RelativeMove>'.format(self.create_profile_token(profile_token), pantilt, pantilts)
        return self.sendSoapMsg(bmsg)

    def relativeMoveZoom(self, profile_token, z, zspeed="0.5"):
        zoom = '<Zoom x="{}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(z)
        zoomspeed = '<Speed><Zoom x="{}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/ZoomGenericSpeedSpace" xmlns="http://www.onvif.org/ver10/schema"/></Speed>'.format(zspeed)
        bmsg = '<RelativeMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}<Translation>{}</Translation>{}</RelativeMove>'.format(self.create_profile_token(profile_token), zoom, zoomspeed)
        return self.sendSoapMsg(bmsg)

    def absoluteMove(self, profile_token, x, y, z):
        pantilt = '<PanTilt x="{}" y="{}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(x,y)
        zoom = '<Zoom x="{}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(z)
        bmsg = '<AbsoluteMove xmlns="http://www.onvif.org/ver20/ptz/wsdl"><Position>{}{}</Position></AbsoluteMove>'.format(self.create_profile_token(profile_token), pantilt, zoom)
        return self.sendSoapMsg(bmsg)

    def continuousMove(self, profile_token, x, y):
        pantilt = '<PanTilt x="{}" y="{}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(x, y)
        bmsg = ' <ContinuousMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}<Velocity>{}</Velocity></ContinuousMove>'.format(self.create_profile_token(profile_token), pantilt)
        return self.sendSoapMsg(bmsg)

    def stopMove(self, profile_token, ptstop="false", zstop="false"):
        pantilt = '<PanTilt>{}</PanTilt>'.format(ptstop)
        zoom = '<Zoom>{}</Zoom>'.format(zstop)
        bmsg = '<Stop xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}{}{}</Stop>'.format(self.create_profile_token(profile_token), pantilt, zoom)
        return self.sendSoapMsg(bmsg)

    def continuousZoom(self, profile_token, z):
        zoom = '<Zoom x="{}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace" xmlns="http://www.onvif.org/ver10/schema"/>'.format(z)
        bmsg = '<ContinuousMove xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}<Velocity>{}</Velocity></ContinuousMove>'.format(self.create_profile_token(profile_token), zoom)
        return self.sendSoapMsg(bmsg)

    # Camera preset use and manipulation

    def setPreset(self, profile_token, presetname):
        preset = '<PresetName{}</PresetName>'.format(presetname)
        bmsg = '<SetPreset xmlns="http://www.onvif.org/ver20/ptz/wsdl"></SetPreset>'.format(self.create_profile_token(profile_token), preset)
        return self.sendSoapMsg(bmsg)

    def getPresets(self, profile_token):
        bmsg = '<GetPresets xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}</GetPresets>'.format(self.create_profile_token(profile_token))
        return self.sendSoapMsg(bmsg)

    def gotoPreset(self, profile_token, preset_token, xspeed="0.5", yspeed="0.5", zspeed="0.5"):
        preset  = '<PresetToken>{}</PresetToken>'.format(preset_token)
        pantiltspeed= '<PanTilt x="{}" y="{}" xmlns="http://www.onvif.org/ver10/schema"/>'.format(xspeed, yspeed)
        speeddetail = '<Speed>{}<Zoom x="{}" xmlns="http://www.onvif.org/ver10/schema"/></Speed>'.format(pantiltspeed, zspeed)
        bmsg = '<GotoPreset xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}{}{}</GotoPreset>'.format(self.create_profile_token(profile_token), preset, speeddetail)
        return self.sendSoapMsg(bmsg)

    def removePreset(self, profile_token, preset_token):
        preset  = '<PresetToken>{}</PresetToken>'.format(preset_token)
        bmsg = '<RemovePreset xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}{}</RemovePreset>'.format(self.create_profile_token(profile_token), preset)
        return self.sendSoapMsg(bmsg)

    # Camera features

    def getVideoSources(self):
        bmsg= '<GetVideoSources xmlns="http://www.onvif.org/ver10/media/wsdl"/>'
        return self.sendSoapMsg(bmsg)

    def getStreamUri(self, profile_token):
        stream = '<Stream xmlns="http://www.onvif.org/ver10/schema">RTP-Unicast</Stream>'
        protocol = '<Protocol>RTSP</Protocol>'
        transport = '<Transport xmlns="http://www.onvif.org/ver10/schema">{}</Transport>'.format(protocol)
        streamsetup = '<StreamSetup>{}{}</StreamSetup>'.format(stream, transport)
        bmsg = '<GetStreamUri xmlns="http://www.onvif.org/ver10/media/wsdl">{}{}</GetStreamUri>'.format(streamsetup, self.create_profile_token(profile_token))
        return self.sendSoapMsg(bmsg)

    def getSnapshotUri(self, profile_token):
        bmsg= '<GetSnapshotUri xmlns="http://www.onvif.org/ver10/media/wsdl">{}</GetSnapshotUri>'.format(self.create_profile_token(profile_token))
        return self.sendSoapMsg(bmsg)

    def getConfigurations(self, profile_token):
        bmsg = '<GetConfigurations xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}</GetConfigurations>'.format(self.create_profile_token(profile_token))
        return self.sendSoapMsg(bmsg)

    def getConfigurationOptions(self, configuration_token):
        config = '<ConfigurationToken>{}</ConfigurationToken>'.format(configuration_token)
        bmsg = '<GetConfigurationOptions xmlns="http://www.onvif.org/ver20/ptz/wsdl">{}</GetConfigurationOptions>'.format(config)
        return self.sendSoapMsg(bmsg)

    def getVideoEncoderConfigurations(self, profile_token):
        bmsg = '<GetVideoEncoderConfigurationOptions xmlns="http://www.onvif.org/ver10/media/wsdl">{}</GetVideoEncoderConfigurationOptions>'.format(self.create_profile_token(profile_token))
        return self.sendSoapMsg(bmsg)
