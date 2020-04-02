import json
import string
import random
import datetime

from filip import config


import logging

log = logging.getLogger('iot')



class DeviceGroup:
    """
    For every Device Group, the pair (resource, apikey) must be unique
    (as it is used to identify which group to assign to which device).
    Those operations of the API targeting specific resources will need
    the use of the resource and apikey parameters to select the
    apropriate instance.

    :param name:    Service of the devices of this type
    :param path:    Subservice of the devices of this type.
    :param cbHost: Context Broker connection information. This options
    can be used to override the global ones for specific types of devices.
    :ivar resource: string representing the Soutbound resource that will be used to assign a type to a device
            (e.g. pathname in the soutbound port)
    :ivar apikey: API key string
    :ivar timestamp: Optional flag whether to include TimeInstant wihtin each entity created, as well als
            TimeInstant metadata to each attribute, with the current Timestamp
    :ivar entity_type: Name of the type to assign to the group.
    :ivar trust: Trust token to use for secured access to the Context Broker
    for this type of devices (optional; only needed for secured scenarios).
    :ivar lazy: List of lazy attributes of the device.
    :ivar commands: List of commands of the device
    :ivar attributes: List of active attributes of the device.
    :ivar static_attributes: List of static attributes to append to the entity. All the updateContext requests to the CB will have this set of attributes appended.
    :ivar internal_attributes: Optional section with free format, to allow
    :ivar autoprovsion: (optional, boolean): If true, APPEND is used upon measure arrival (thus effectively allowing autoprovisioned devices). If false, UPDATE is used open measure arrival (thus effectively avoiding autoprovisioned devices). This field is optional, so if it omitted then the global IoTAgent appendModel configuration is used.
    specific IoT Agents to store information along with the devices in the Device Registry.
    """
    def __init__(self, fiware_service ,
                 cb_host: str, **kwargs):

        self.__service = fiware_service.name
        self.__subservice = fiware_service.path
        self.__cbHost = cb_host

        self.__resource = kwargs.get("resource", "/iot/d") #for iot-ul 1.7.0
        # the default must be empty string
        self.__apikey = kwargs.get("apikey", "12345")
        self.timestamp = kwargs.get("timestamp", None)
        self.autoprovision = kwargs.get("autoprovision", None)
        self.__entity_type = kwargs.get("entity_type", "Thing")
        self.trust = kwargs.get("trust")
        self.__lazy = kwargs.get("lazy", [])
        self.__commands = kwargs.get("commands", [])
        self.__attributes = kwargs.get("attributes", [])
        self.__static_attributes = kwargs.get("static_attributes", [])
        self.__internal_attributes = kwargs.get("internal_attributes", [])

        self.devices = []
        self.__agent = kwargs.get("iot-agent", "iota-json")


        #For using the update functionality, the former configuration needs
        # to be stored
        self.__service_last = fiware_service.name
        self.__subservice_last = fiware_service.path
        self.__resource_last = kwargs.get("resource", "/iot/d")
        self.__apikey_last = kwargs.get("apikey", "12345")

    def update(self,**kwargs):
        #For using the update functionality, the former configuration needs
        # to be stored
        # TODO: NOTE: It is not recommenend to change the combination fiware
        #  service structure and apikey --> Delete old and register a new one
        self.__service_last = self.__service
        self.__subservice_last = self.__subservice
        self.__resource_last = self.__resource
        self.__apikey_last = self.__apikey

        # From here on the variables are updated
        self.__service = kwargs.get("fiware_service", self.__service)
        self.__subservice = kwargs.get("fiware_service_path",
                                       self.__subservice)
        self.__resource = kwargs.get("resource", self.__resource)  # for iot-ul 1.7.0
        # the default must be empty string
        self.__apikey = kwargs.get("apikey", self.__apikey)
        self.__entity_type = kwargs.get("entity_type", self.__entity_type)
        # self.trust
        self.__cbHost = kwargs.get("cb_host", self.__cbHost)
        self.__lazy = kwargs.get("lazy", self.__lazy)
        self.__commands = kwargs.get("commands", self.__commands)
        self.__attributes = kwargs.get("attributes", self.__attributes)
        self.__static_attributes = kwargs.get("static_attributes",
                                              self.__static_attributes)
        self.__internal_attributes = kwargs.get("internal_attributes",
                                                self.__internal_attributes)

        self.__devices = []
        self.__agent = kwargs.get("iot-agent", self.__agent)

    def add_lazy(self, attribute):
        self.__lazy.append(attribute)

    def add_active(self, attribute):
        self.__attributes.append(attribute)

    def add_static(self, attribute):
        self.__static_attributes.append(attribute)

    def add_command(self, attribute):
        self.__commands.append(attribute)

    def add_internal(self, attribute):
        self.__internal_attributes.append(attribute)

    def get_resource(self):
        return self.__resource

    def get_apikey(self):
        return self.__apikey

    def add_default_attribute(self, attribute:dict):
        """
        :param name: The name of the attribute as submitted to the context broker.
        :param type: The type of the attribute as submitted to the context broker.
        :param object_id: The id of the attribute used from the southbound API.
        :param attr_type: One of \"active\" (default), \"lazy\" or \"static\"
        """

        attr_type = attribute["attr_type"]
        if "attr_value" in attribute:
            if (attr_type!= "static") or (attr_type != "internal"):# & attribute["attr_value"] != None:
                log.warning("Setting attribute value only allowed for static or internal attributes! Value will be ignored!")
                del attribute["attr_value"]

        attr = {"name": attribute["name"],
                "type": attribute["value_type"]
                }
        # static attribute do not need an object id
        if attr_type != "static":
            attr["object_id"] = attribute["object_id"]


        switch_dict = {"active": self.add_active,
                        "lazy": self.add_lazy,
                        "static":  self.add_static,
                        "command": self.add_command,
                        "internal": self.add_internal
                       }.get(attr_type, "not_ok")(attr)
        if switch_dict == "not_ok":
            log.warning(f" {datetime.datetime.now()} - Attribute type unknown: {attr_type}")

    def delete_default_attribute(self, attr_name, attr_type):
        '''
        Removing attribute by name and from the list of attributes in the
        local device group. You need to execute update device in iot agent in
        order to update the configuration to remote!
        :param attr_name: Name of the attribute to delete
        :param attr_type: Type of the attribute to delte
        :return:
        '''
        try:
            if attr_type == "active":
                self.__attributes = [i for i in self.__attributes if not (i[
                                                        'name']==attr_name)]
            elif attr_type == "lazy":
                self.__lazy = [i for i in self.__lazy if not (i['name'] ==
                                                                   attr_name)]
            elif attr_type == "static":
                self.__static_attributes = [i for i in
                                            self.__static_attributes
                                            if not (
                            i['name'] == attr_name)]
            elif attr_type == "internal":
                self.__internal_attributes = [i for i in
                                              self.__internal_attributes
                                              if not
                                              (i['name'] ==  attr_name)]
            elif attr_type == "command":
                self.__commands = [i for i in self.__commands if not
                (i['name'] == attr_name)]

            else:
                log.warning(f" {datetime.datetime.now()} - Attribute type unknown: {attr_type}")

            log.info(f" {datetime.datetime.now()} - Attribute succesfully deleted: {attr_name}")
        except:
            log.warning(f" {datetime.datetime.now()} - Attribute could not be deleted: {attr_name}")


    def get_apikey(self):
        return self.__apikey

    def get_resource(self):
        return self.__resource

    def get_apikey_last(self):
        return self.__apikey_last

    def get_resource_last(self):
        return self.__resource_last


    def get_header(self) -> dict:
        return {
            "fiware-service": self.__service,
            "fiware-servicepath": self.__subservice
        }

    def get_header_last(self) -> dict:
        return {
            "fiware-service": self.__service_last,
            "fiware-servicepath": self.__subservice_last
        }

    def get_json(self):
        dict = {}
        dict['apikey']= self.__apikey
        dict['cbroker'] = self.__cbHost
        dict['entity_type'] = self.__entity_type
        dict['resource'] = self.__resource
        dict['lazy'] = self.__lazy
        dict['attributes'] = self.__attributes
        dict['commands'] = self.__commands
        dict['static_attributes'] = self.__static_attributes
        dict['internal_attributes'] = self.__internal_attributes
        if self.timestamp!=None:
            dict['timestamp']=self.timestamp
        if self.autoprovision!=None:
            dict['autoprovision']=self.autoprovision
        return json.dumps(dict, indent=4)

    def generate_apikey(self, length: int = 10):
        """
        This function generates a random key from lowercase letter and
        digit characters
        :ivar length: Number of characters in the key string
        """
        return ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(
            length))

    def test_apikey(self):
        """
        This function tests if an apikey is defined in the configfile.
        Otherwise it will ask the user to generate one and saves it to the
        configfile in the given sections.
        """
        try:
            if self.__apikey == "":
                res = input("[INFO]: No API-Key defined. Do you want to "
                            "generate one? "
                            "y/Y ")
                if res == "y" or res == "Y":
                    res = input("Please specify number of key (default is "
                                "10)? ")
                    if res != 10:
                        self.__apikey = self.generate_apikey(int(res))
                    else:
                        self.__apikey = self.generate_apikey()
                    #with open(self.path, 'w') as configfile:
                    #    self.config.write(configfile)
                    log.info(f" {datetime.datetime.now()} - Random Key generated: {self.__apikey}")
                else:
                    log.info(f" {datetime.datetime.now()} - Default Key will be used: 1234")

            log.info(f" {datetime.datetime.now()} - API-Key check success! {self.__apikey}")
        except Exception:
            log.error(f" {datetime.datetime.now()} - API-Key check failed. Please check configuration!")


    def __repr__(self):
        """
        Function returns a representation of the object (its data) as a string.
        :return:
        """
        return "{}".format(self.get_json())
