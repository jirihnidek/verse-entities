# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
This module includes class VerseLayer representing verse layer at verse
client. This class could be used for sharing list or dictionaries.
"""

import verse as vrs
from . import verse_entity


# TODO: implement all required methods
class VerseLayerItems(dict):
    """
    Class representing items in verse layer. It is subclass of
    Python dictionary. When client set item in dictionary, then
    changed value is sent to the Verse server.
    """

    def __init__(self, layer):
        """
        Constructor of VerseLayerItems
        """
        self.layer = layer


    def __setitem__(self, key, value):
        """
        Setter of item that tries to send new value to Verse server
        """
        # TODO: simplify following condition
        if self.layer.node.session is not None and self.layer.id is not None and self.layer.send_cmds == True:
            self.layer.node.session.send_layer_set_value(self.layer.node.prio, \
                self.layer.node.id, \
                self.layer.id, \
                key, \
                value)
        return super(VerseLayerItems, self).__setitem__(key, value)


    def pop(self, key):
        """
        Pop item from dict that tries to unset value at Verse server
        """
        if self.layer.node.session is not None and self.layer.id is not None:
            self.layer.node.session.send_layer_unset_value(self.layer.node.prio, \
                self.layer.node.id, \
                self.layer.id, \
                key)
        return super(VerseLayerItems, self).pop(key)


    def popitem(self):
        """
        Pop some item from dictionary and tries to unset this value at Verse server
        """
        key, value = super(VerseLayerItems, self).popitem()
        if self.layer.node.session is not None and self.layer.id is not None:
            self.layer.node.session.send_layer_unset_value(self.layer.node.prio, \
                self.layer.node.id, \
                self.layer.id, \
                key)
        return (key, value)




class VerseLayer(verse_entity.VerseEntity):
    """
    Class representing Verse layer. Verse layer is entity that could share
    dictionary like data structures.
    """


    def __init__(self, node, parent_layer=None, layer_id=None, data_type=None, count=1, custom_type=None):
        """
        Constructor of VerseLayer
        """
        super(VerseLayer, self).__init__(custom_type=custom_type)
        self.node = node
        self.id = layer_id
        self.data_type = data_type
        self.count = count
        self.child_layers = {}
        self.items = VerseLayerItems(self)
        self.parent_layer = parent_layer
        self.send_cmds = True

        # Change state and send commands
        self._create()

        # Set bindings
        if layer_id is not None:
            self.node.layers[layer_id] = self
        else:
            self.node.layer_queue[self.custom_type] = self
        if self.parent_layer is not None and layer_id is not None:
            self.parent_layer.child_layers[layer_id] = self


    def _send_create(self):
        """
        Send layer create to Verse server
        """
        if self.node.session is not None and self.id is not None:
            if self.parent_layer is not None:
                self.node.session.send_layer_create(self.node.prio, \
                    self.node.id, \
                    self.parent_layer.id, \
                    self.data_type, \
                    self.count, \
                    self.custom_type)
            else:
                self.node.session.send_layer_create(self.node.prio, \
                    self.node.id, \
                    -1, \
                    self.data_type, \
                    self.count, \
                    self.custom_type)


    def _send_destroy(self):
        """
        Send layer destroy command to Verse server
        """
        if self.node.session is not None and self.id is not None:
            self.node.session.send_layer_destroy(self.node.prio, self.node.id, self.id)


    def _send_subscribe(self):
        """
        Send layer subscribe command to Verse server
        """
        if self.node.session is not None and self.id is not None:
            self.node.session.send_layer_subscribe(self.node.prio. self.node.id, self.id, self.version, self.crc32)


    def _send_unsubscribe(self):
        """
        Send layer unsubscribe to Verse server
        """
        if self.node.session is not None and self.id is not None:
            self.node.session.send_layer_unsubscribe(self.node.prio, self.node.id, self.id, self.version, self.crc22)


    def _clean(self):
        """
        This method clean all data from this object
        """
        # Clean all child nodes, but do not send destroy commands
        # for them, because Verse server do this automaticaly too
        for layer in self.child_layers.values():
            layer.parent_layer = None
            layer._clean()
        self.child_layers.clear()
        self.node.layers.pop(self.id)


    def destroy(self):
        """
        Change state of entity and send destroy command to Verse server
        """
        self._destroy()

    
    @staticmethod
    def _receive_layer_create(session, node_id, parent_layer_id, layer_id, data_type, count, custom_type):
        """
        Static method of class that add reference to the
        the dictionary of layers and send pending layer set values
        """

        # Try to find node
        node = None
        try:
            node = session.nodes[node_id]
        except KeyError:
            return

        # Try to find/create parent layer
        if parent_layer_id is not None:
            try:
                parent_layer = node.layers[parent_layer_id]
            except KeyError:
                # When new layer has parent layer, but this parent layer does not exist yet, then
                # create this parent layer ... TODO: this is fishy
                #parent_layer = VerseLayer(node=node, parent_layer=None, layer_id=parent_layer_id)
                parent_layer = None
        else:
            parent_layer = None

        # Try to find this layer in pending layers of node. otherwise create new layer
        try:
            layer = node.layer_queue[custom_type]
            layer.id = layer_id
        except KeyError:
            layer = VerseLayer(node=node, \
                parent_layer=parent_layer, \
                layer_id=layer_id, \
                data_type=data_type, \
                count=count, \
                custom_type=custom_type)

        node.layers[layer_id] = layer

        # When this layer has some pending values, then send them to Verse server
        for item_id, value in layer.items.items():
            session.send_layer_set_value(node.prio, node.id, layer.id, item_id, layer.data_type, value)


    @staticmethod
    def _receive_layer_destroy(session, node_id, layer_id):
        """
        Static method of class that remove reference to this layer from
        the dictionary of layers
        """

        # Try to find node
        node = None
        try:
            node = session.nodes[node_id]
        except KeyError:
            return
        # Try to find the layer
        try:
            layer = node.layers[layer_id]
        except KeyError:
            return
        # Destroy layer and child layers
        layer._receive_destroy()

        return layer


    @staticmethod
    def _receive_layer_set_value(session, node_id, layer_id, item_id, value):
        """
        Static method of class that set value of item in layer
        """

        # Try to find node
        node = None
        try:
            node = session.nodes[node_id]
        except KeyError:
            return
        # Try to find the layer
        try:
            layer = node.layers[layer_id]
        except KeyError:
            return
        # Set item value, but do not send command to verse server
        layer.send_cmds = False
        layer.items[item_id] = value
        layer.send_cmds = True

        return layer


    @staticmethod
    def _receive_layer_unset_value(session, node_id, layer_id, item_id):
        """
        Static method of class that set value of item in layer
        """

        # Try to find node
        node = None
        try:
            node = session.nodes[node_id]
        except KeyError:
            return
        # Try to find the layer
        try:
            layer = node.layers[layer_id]
        except KeyError:
            return
        # UnSet item value
        try:
            layer.items.pop(item_id)
        except KeyError:
            return

        return layer


    @staticmethod
    def _receive_layer_subscribe(session, node_id, layer_id, version, crc32):
        """
        Static method of class that should be called when layer
        subscribe command is received from Verse server
        """
        # TODO
        pass


    @staticmethod
    def _receive_layer_unsubscribe(session, node_id, layer_id, version, crc32):
        """
        Static method of class that should be called when layer
        unsubscribe command is received from Verse server
        """
        # TODO
        pass
