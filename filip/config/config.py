import os
import errno
import logging
import logging.config
import yaml
import json

# setup Environmental parameters
TIMEZONE = os.getenv("TIMEZONE", "UTC/Zulu")
LOGLEVEL = os.getenv("LOGLEVEL", "INFO")
logging.basicConfig(level=LOGLEVEL,
                    format='%(asctime)s - FiLiP.%(name)s - %(levelname)s: %('
                              'message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger('config')


def setup_logging(path_to_config: str ='/Users/Felix/PycharmProjects/Logger/filip/log_config.yaml',
                  default_level=logging.INFO):
    """
    Function to setup the logging configuration from a file
    var: path_to_config: a file configuring the logging setup, either a JSON or a YAML
    var: default_level: if no valid config file is present, this sets the default logging level
    """
    if os.path.exists(path_to_config):
        file_extension = (path_to_config.split('.')[-1]).lower()
        with open(path_to_config, 'rt') as file:
            if file_extension in ['yaml', 'yml']:
                cfg = yaml.load(file, Loader=yaml.Loader)
            elif file_extension == 'json':
                cfg = json.load(file)
        logging.config.dictConfig(cfg)
    else:
        logging.basicConfig(level=default_level)

class Config:
    __data={'orion': {},
            'iota': {},
            'quantumleap': {},
            'fiware': {},
            'timezone': os.getenv("TIMEZONE", "UTC/Zulu"),
            'loglevel': os.getenv("LOGLEVEL", "INFO")}

    def __init__(self, path = None, *args, **kwargs):
        """
        Class constructor for config class. At start up it parses either
        system environment variables or external config file in json format.
        If CONFIG_FILE is set to true external config file will be used
        NOTE: If list of parameters is extended do it here and in
        def update_config()
        """
        kwargs=self._lower_dict(kwargs)
        self.__data.update(kwargs)


        self.file = os.getenv("CONFIG_FILE", 'True')
        self.path = os.getenv("CONFIG_PATH", path)

        if eval(self.file):
            log.info(f"CONFIG_PATH variable is updated to: {self.path}")
            self._read_config_file(self.path)
        else:
            log.info("Configuration loaded from environment variables")
            self._read_config_envs()

        # TODO:
        #
        # 0. check if data dict is not None --> use some default values
        # 1. assert data dict

        # self.update_config_param(self.data)
        #try:
#        self.test_services(self.data)
        #except Exception:
         #   pass

            # Needs to go to services
            # self.fiware_service = os.getenv("FIWARE_SERVICE", "default")
            # self.fiware_service_path = os.getenv("FIWARE_SERVICE_PATH",  "/")

    def __repr__(self):
        """
        Returns the Representation (= Data) of the object as string
        :return:
        """
        return json.dumps(self.__data, indent=4)

    def __getitem__(self, item):
        return self.__data.get(item)

    def __setitem__(self, key, value):
        self.__data.__setitem__(key, value)

    def __getattr__(self, item):
        return self.__data.get(item)

    @property
    def data(self):
        return self.__data

    def _lower_dict(self, d):
        lower_dict = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = self._lower_dict(v)
            lower_dict[k.lower()] = v
        return lower_dict

    def _create_servive_urls(self, d):
        for k, v in d.items():
            if k in ['orion', 'iota', 'quantumleap'] and v.get('url',
                                                               None) == None:
                if d[k]['host'].casefold().startswith(('http://',
                                                       'https://')):
                    prefix = ""
                else:
                    prefix = "https://"
                if v.get('port', None) == None:
                    d[k]['url'] = f"{prefix}{d[k]['host']}"
                else:
                    d[k]['url'] = f"{prefix}{d[k]['host']}:{d[k]['port']}"
        return d

    def _read_config_file(self, path: str):
        """
        Reads configuration file and stores data in entity CONFIG
        :param path: Path to config file
        :return: True if operation works
        :return: False if operation fails
        """
        #TODO: add use of ini: do strings processing split at last dot (if .json or .ini)
        #TODO: check if all data is defined
        try:
            if path.endswith('.json'):
                with open(path, 'r') as filename:
                    log.info(f"Reading {path}")
                    data = json.load(filename)

        except IOError as err:
            if err.errno == errno.ENOENT:
                log.error(f"{path} - does not exist")
            elif err.errno == errno.EACCES:
                log.error(f"{path}- cannot be read")
            else:
                log.error(f"{path}- some other error")
            return False

        data = self._lower_dict(data)
        data = self._create_servive_urls(data)

        log.info(json.dumps(data, indent=4))

        self.__data.update(data)

    def _read_config_envs(self):
        """
        reads environment variables for host urls and ports of orion, IoTA,
        quantumleap, crate. Default URL of Orion is "http://localhost", 
        the default ULR of IoTA, quantumleap and Crate is the URL of Orion.
        """
        data=self.__data
        data['orion']['host'] = os.getenv("ORION_HOST", "localhost")
        data['orion']['port'] = int(os.getenv("ORION_PORT", 1026))
        data['orion']['url'] = os.getenv("ORION_URL", None)

        data['iota']['host'] = os.getenv("IOTA_HOST", data['orion']['host'])
        data['iota']['port'] = int(os.getenv("IOTA_PORT", 4041))
        data['iota']['url'] = os.getenv("IOTA_URL", None)
        data['iota']['protocol'] = os.getenv("IOTA_PROTOCOL", "IoTA-UL") # or IoTA-JSON

        data['quantumleap']['host'] = os.getenv("QUANTUMLEAP_HOST",
                                                data['orion']['host'])
        data['quantumleap']['port'] = int(os.getenv("QUANTUMLEAP_PORT", 8668))
        data['quantumleap']['url'] = os.getenv("QUANTUMLEAP_URL", None)

        data['fiware']['service'] = os.getenv("FIWARE_SERVICE",
                                              "dummy_service")
        data['fiware']['service_path'] = os.getenv("FIWARE_SERVICE_PATH",
                                                   "/dummy_path")

        data = self._create_servive_urls(data)
        log.info(json.dumps(data, indent=4))

        self.__data.update(data)

    def update_config_param(self, data: dict):
        """
        This function updates the parameters of class config
        :param data: dict coming from parsing config file or environment
        varibles
        :return:
        """
        try:
            self.data = data
            log.info("Configuration parameters updated:")
            log.info(json.dumps(data, indent=4))
        except Exception:
            print("[ERROR]: Failed to set config parameters!")
            pass
        '''try:
            self.orion_host = data['orion']['host']
            self.orion_port = data['orion']['port']
            self.iota_host = data['iota']['host']
            self.iota_port = data['iota']['port']
            self.quantumleap_host = data['quantum_leap']['host']
            self.quantumleap_port = data['quantum_leap']['port']
            print("[INFO]: Configuration parameters updated:")
            print(json.dumps(data, indent=4))
        except Exception:
            print("[ERROR]: Failed to set config parameters!")
            pass
        return True'''
        
# TODO: move to single services
#    def test_services(self, config: dict):
#        """This function checks the configuration and tests connections to
#        necessary server endpoints"""
#        test.test_config('orion', config)
#        test.test_connection('Orion Context Broker', self.data['orion'][
#            'host'] + ':' + str(self.data['orion']['port']) + '/version')
#        test.test_config('iota', config)
#        test.test_connection('IoT Agent JSON', self.data['iota'][
#            'host'] + ':' + str(self.data['iota']['port']) + '/iot/about')
#        test.test_config('quantum_leap', config)
#        test.test_connection('Quantum Leap', self.data['quantum_leap'][
#            'host'] + ':' + str(self.data['quantum_leap']['port']) + \
#        '/v2/version')
#        print("[INFO]: Configuration seems fine!")


class Log_Config:
    def __init__(self, path = None):
        """
        Class constructor for config class. At start up it parses either
        system environment variables or external config file in json format.
        If CONFIG_FILE is set to true external config file will be used
        NOTE: If list of parameters is extended do it here and in
        def update_config()
        """
        self.file = os.getenv("CONFIG_FILE", 'True')
        self.path = os.getenv("CONFIG_PATH", path)
        self.data = None
        if eval(self.file):
            log.info(f"CONFIG_PATH variable is updated to: {self.path}")
            self.data = self._read_config_file(self.path)
        else:
            log.info("Configuration loaded from environment variables")
            self.data = self._read_config_envs()
        if self.data is not None:
            pass
        # TODO:
        # 0. check if data dict is not None --> use some default values
        # 1. assert data dict

        # self.update_config_param(self.data)
        # try:
        #   self.test_services(self.data)
        #except Exception:
        #   pass

            # Needs to go to services
            # self.fiware_service = os.getenv("FIWARE_SERVICE", "default")
            # self.fiware_service_path = os.getenv("FIWARE_SERVICE_PATH",  "/")

    def _read_config_file(self, path: str):
        """
        Reads configuration file and stores data in entity CONFIG
        :param path: Path to config file
        :return: True if operation works
        :return: False if operation fails
        """
        #TODO: add use of ini: do strings processing split at last dot (if .json or .ini)
        #TODO: check if all data is defined
        try:
            file_extension = path.split(".")[1]
            with open(path, 'rt') as f:
                if file_extension in ['yaml', 'yml']:
                    cfg = yaml.load(f, Loader=yaml.Loader)
                elif file_extension == 'json':
                    cfg = json.load(f)
                logging.config.dictConfig(cfg)

                print(json.dumps(cfg, indent=4))

        except IOError as err:
            if err.errno == errno.ENOENT:
                log.error(f"{path} - does not exist")
            elif err.errno == errno.EACCES:
                log.error(f"{path}- cannot be read")
            else:
                log.error(f"{path}- some other error")
            return False
        return cfg


    def _read_config_envs(self):
        """
        reads envrionment variables for module loggers. The default setting is DEBUG
        """
        cfg = {}
        cfg["version"] = 1
        cfg["disable_existing_loggers"] = False
        cfg["formatters"]["standard"]["format"] = os.getenv("LOG_FORMAT_STANDARD",
                                                            "%(asctime)s-%("
                                                            "levelname)s-filip.%(name)s: "
                                                            "%(message)s")
        cfg["formatters"]["error"]["format"] = os.getenv("LOG_FORMAT_ERROR",
                                                         "%(asctime)s-%("
                                                         "levelname)s <PID %("
                                                         "process)d:%("
                                                         "processName)s> "
                                                         "filip.%(name)s.%("
                                                         "funcName)s(): %(message)s" )

        cfg["handlers"]["console"]["class"] = os.getenv("LOG_CLASS_CONSOLE", "logging.StreamHandler")
        cfg["handlers"]["console"]["level"] = os.getenv("LOG_LEVEL_CONSOLE", "DEBUG")
        cfg["handlers"]["console"]["formatter"] = os.getenv("LOG_FORMATTER_CONSOLE", "standard")
        cfg["handlers"]["console"]["class"] = os.getenv("LOG_STREAM_CONSOLE", "ext://sys.stdout")

        cfg["handlers"]["info_file_handler"]["class"] = os.getenv("LOG_CLASS_INFO", "logging.handlers.RotatingFileHandler")
        cfg["handlers"]["info_file_handler"]["level"] = os.getenv("LOG_LEVEL_INFO", "INFO")
        cfg["handlers"]["info_file_handler"]["formatter"] = os.getenv("LOG_FORMATTER_INFO", "standard")
        cfg["handlers"]["info_file_handler"]["filename"] = os.getenv("LOG_FILENAME_INFO", "info.logger")
        cfg["handlers"]["info_file_handler"]["maxBytes"] = os.getenv("LOG_MAXBYTES_INFO", 10485760)
        cfg["handlers"]["info_file_handler"]["backupCount"] = os.getenv("LOG_BACKUPCOUNT_INFO", 20)
        cfg["handlers"]["info_file_handler"]["encoding"] = os.getenv("LOG_ENCODING_INFO", "utf8")

        cfg["handlers"]["error_file_handler"]["class"] = os.getenv("LOG_CLASS_ERROR", "logging.handlers.RotatingFileHandler")
        cfg["handlers"]["error_file_handler"]["level"] = os.getenv("LOG_LEVEL_ERROR", "ERROR")
        cfg["handlers"]["error_file_handler"]["formatter"] = os.getenv("LOG_FORMATTER_ERROR", "error")
        cfg["handlers"]["error_file_handler"]["filename"] = os.getenv("LOG_FILENAME_ERROR", "error.logger")
        cfg["handlers"]["error_file_handler"]["maxBytes"] = os.getenv("LOG_MAXBYTES_ERROR", 10485760)
        cfg["handlers"]["error_file_handler"]["backupCount"] = os.getenv("LOG_BACKUPCOUNT_ERROR", 20)
        cfg["handlers"]["error_file_handler"]["encoding"] = os.getenv("LOG_ENCODING_ERROR", "utf8")

        cfg["handlers"]["debug_file_handler"]["class"] = os.getenv("LOG_CLASS_DEBUG", "logging.handlers.RotatingFileHandler")
        cfg["handlers"]["debug_file_handler"]["level"] = os.getenv("LOG_LEVEL_DEBUG", "DEBUG")
        cfg["handlers"]["debug_file_handler"]["formatter"] = os.getenv("LOG_FORMATTER_DEBUG", "error")
        cfg["handlers"]["debug_file_handler"]["filename"] = os.getenv("LOG_FILENAME_DEBUG", "debug.logger")
        cfg["handlers"]["debug_file_handler"]["maxBytes"] = os.getenv("LOG_MAXBYTES_DEBUG", 10485760)
        cfg["handlers"]["debug_file_handler"]["backupCount"] = os.getenv("LOG_BACKUPCOUNT_DEBUG", 20)
        cfg["handlers"]["debug_file_handler"]["encoding"] = os.getenv("LOG_ENCODING_DEBUG", "utf8")

        cfg["loggers"]["iot"]["level"] = os.getenv("LOGGER_LEVEL_IOT",
                                                     "DEBUG")
        cfg["loggers"]["iot"]["handlers"] = os.getenv(
            "LOGGER_HANDLERS_IOT", ["console", "info_file_handler",
                                                                              "error_file_handler", "debug_file_handler"])
        cfg["loggers"]["iot"]["propagate"] = os.getenv(
            "LOGGER_PROPAGATE_IOT", "no")

        cfg["loggers"]["orion"]["level"] = os.getenv(
            "LOGGER_LEVEL_ORION",
                                                      "DEBUG")
        cfg["loggers"]["orion"]["handlers"] = os.getenv(
            "LOGGER_HANDLERS_ORION", ["console", "info_file_handler",
                                                                                  "error_file_handler", "debug_file_handler"])
        cfg["loggers"]["orion"]["propagate"] = os.getenv(
            "LOGGER_PROPAGATE_ORION", "no")

        cfg["loggers"]["subscription"]["level"] = os.getenv("LOGGER_LEVEL_SUBSCRIPTION", "DEBUG")
        cfg["loggers"]["subscription"]["handlers"] = os.getenv("LOGGER_HANDLERS_SUBSCRIPTION", ["console", "info_file_handler",
                                                                                                "error_file_handler", "debug_file_handler"])
        cfg["loggers"]["subscription"]["propagate"] = os.getenv("LOGGER_PROPAGATE_SUBSCRIPTION", "no")

        cfg["loggers"]["timeseries"]["level"] = os.getenv("LOGGER_LEVEL_TIMESERIES", "DEBUG")
        cfg["loggers"]["timeseries"]["handlers"] = os.getenv("LOGGER_HANDLERS_TIMESERIES", ["console", "info_file_handler",
                                                                                            "error_file_handler", "debug_file_handler"])
        cfg["loggers"]["timeseries"]["propagate"] = os.getenv("LOGGER_PROPAGATE_TIMESERIES", "no")


        cfg["root"]["level"] = os.getenv("LOGGER_LEVEL_ROOT", "DEBUG")
        cfg["root"]["handlers"] = os.getenv("LOGGER_HANDLERS_ROOT", ["console", "info_file_handler",
                                                              "error_file_handler", "debug_file_handler"])

        logging.config.dictConfig(cfg)

        return cfg


    def update_config_param(self, data: dict):
        """
        This function updates the parameters of class config
        :param data: dict coming from parsing config file or environment
        varibles
        :return:
        """
        try:
            self.data = data
            log.info("Configuration parameters updated:")
            print(json.dumps(data, indent=4))
        except Exception:
            log.error("Failed to set config parameters!")
            pass


if __name__=="__main__":
    CONFIG = Config('/Users/Felix/PycharmProjects/compare_duplicate/filip/config.json')
    #print(CONFIG.data['fiwareService'])

    LOG_CONFIG = Log_Config("/Users/Felix/PycharmProjects/compare_duplicate/filip/log_config.json")
    print("List of services and paths:")
    for service in CONFIG.data['fiwareService']:
        print("{:<30}{:<20}".format('Service: ', service['service']))
        for path in service['service_path']:
            print("{:<30}{:<40}".format('', path))
