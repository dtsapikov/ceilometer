# -*- encoding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc
#
# Author: Eoghan Glynn <eglynn@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Handler for producing image counter messages from glance notification
   events.
"""

from oslo.config import cfg

from ceilometer import counter
from ceilometer import plugin

OPTS = [
    cfg.StrOpt('glance_control_exchange',
               default='glance',
               help="Exchange name for Glance notifications"),
]


cfg.CONF.register_opts(OPTS)


class ImageBase(plugin.NotificationBase):
    """Base class for image counting."""

    @staticmethod
    def get_exchange_topics(conf):
        """Return a sequence of ExchangeTopics defining the exchange and
        topics to be connected for this plugin.
        """
        return [
            plugin.ExchangeTopics(
                exchange=conf.glance_control_exchange,
                topics=set(topic + ".info"
                           for topic in conf.notification_topics)),
        ]


class ImageCRUDBase(ImageBase):
    @staticmethod
    def get_event_types():
        return [
            'image.update',
            'image.upload',
            'image.delete',
        ]


class ImageCRUD(ImageCRUDBase):
    def process_notification(self, message):
        yield counter.Counter.from_notification(
            name=message['event_type'],
            type=counter.TYPE_DELTA,
            unit='image',
            volume=1,
            resource_id=message['payload']['id'],
            user_id=None,
            project_id=message['payload']['owner'],
            message=message)


class Image(ImageCRUDBase):
    def process_notification(self, message):
        yield counter.Counter.from_notification(
            name='image',
            type=counter.TYPE_GAUGE,
            unit='image',
            volume=1,
            resource_id=message['payload']['id'],
            user_id=None,
            project_id=message['payload']['owner'],
            message=message)


class ImageSize(ImageCRUDBase):
    def process_notification(self, message):
        yield counter.Counter.from_notification(
            name='image.size',
            type=counter.TYPE_GAUGE,
            unit='B',
            volume=message['payload']['size'],
            resource_id=message['payload']['id'],
            user_id=None,
            project_id=message['payload']['owner'],
            message=message)


class ImageDownload(ImageBase):
    """Emit image_download counter when an image is downloaded."""
    @staticmethod
    def get_event_types():
        return [
            'image.send',
        ]

    def process_notification(self, message):
        yield counter.Counter.from_notification(
            name='image.download',
            type=counter.TYPE_DELTA,
            unit='B',
            volume=message['payload']['bytes_sent'],
            resource_id=message['payload']['image_id'],
            user_id=message['payload']['receiver_user_id'],
            project_id=message['payload']['receiver_tenant_id'],
            message=message)


class ImageServe(ImageBase):
    """Emit image_serve counter when an image is served out."""
    @staticmethod
    def get_event_types():
        return [
            'image.send',
        ]

    def process_notification(self, message):
        yield counter.Counter.from_notification(
            name='image.serve',
            type=counter.TYPE_DELTA,
            unit='B',
            volume=message['payload']['bytes_sent'],
            resource_id=message['payload']['image_id'],
            user_id=None,
            project_id=message['payload']['owner_id'],
            message=message)
