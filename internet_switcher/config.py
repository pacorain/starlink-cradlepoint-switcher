# SPDX-License-Identifier: Unlicense

import configparser
import os

import logging
from typing import MutableMapping

logger = logging.getLogger(__name__)

class Config:
    __slots__ = (
        'cradlepoint_ip_address',
        'cradlepoint_port',
        'cradlepoint_username',
        'cradlepoint_password',
        'starlink_ip_address',
        'starlink_port'
    )

    def __init__(self):
        self.cradlepoint_ip_address = '192.168.0.1'
        self.cradlepoint_port = '80'
        self.cradlepoint_username = 'admin'
        self.cradlepoint_password = 'admin'
        self.starlink_ip_address = '192.168.100.1'
        self.starlink_port = '9200'

    @classmethod
    def load(cls):
        """Loads the configuration from multiple default sources.
        
        The configuration is loaded in a specific order."""
        config = cls()
        config.set_from_config()
        config.set_from_env()
        return config

    @classmethod
    def from_env(cls):
        config = cls()
        config.set_from_env()
        return config

    def set_from_env(self):
        self.cradlepoint_ip_address = os.getenv('CRADLEPOINT_IP_ADDRESS', self.cradlepoint_ip_address)
        self.cradlepoint_port = os.getenv('CRADLEPOINT_PORT', self.cradlepoint_port)
        self.cradlepoint_username = os.getenv('CRADLEPOINT_USERNAME', self.cradlepoint_username)
        self.cradlepoint_password = os.getenv('CRADLEPOINT_PASSWORD', self.cradlepoint_password)
        self.starlink_ip_address = os.getenv('STARLINK_IP_ADDRESS', self.starlink_ip_address)
        self.starlink_port = os.getenv('STARLINK_PORT', self.starlink_port)

        return self

    @classmethod
    def from_config(cls, config_path='config.ini'):
        config = cls()
        config.set_from_config(config_path)
        return config

    def set_from_config(self, config_path='config.ini'):
        parser = configparser.ConfigParser()
        with open(config_path, 'r') as f:
            parser.read_file(f)

        if 'cradlepoint' in parser:
            cradlepoint_config = parser['cradlepoint']
            self.cradlepoint_ip_address = cradlepoint_config.get('ip_address', self.cradlepoint_ip_address)
            self.cradlepoint_port = cradlepoint_config.get('port', self.cradlepoint_port)
            self.cradlepoint_username = cradlepoint_config.get('username', self.cradlepoint_username)
            self.cradlepoint_password = cradlepoint_config.get('password', self.cradlepoint_password)

        if 'starlink' in parser:
            starlink_config = parser.get['starlink']
            self.starlink_ip_address = starlink_config.get('ip_address', self.starlink_ip_address)
            self.starlink_port = starlink_config.get('port', self.starlink_port)

        return self

    @property
    def cradlepoint_server(self):
        return self.cradlepoint_ip_address + ":" + self.cradlepoint_port
