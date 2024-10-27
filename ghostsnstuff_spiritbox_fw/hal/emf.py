import gatt
import threading
from typing import Self
from . import platform
from abc import ABC, abstractmethod

SERVICE_UUID = "ad91b201-7347-4047-9e17-3bed82d75f9d"
RECV_CHARACTERISTIC_UUID = "b6fccb50-87be-44f3-ae22-f85485ea42c4"
EMF_MAC_ADDRESS = "64:e8:33:8a:2a:0a"
COMMAND_RESET = 0x00
COMMAND_SLEEP = 0x01
COMMAND_SET_ACTIVITY = 0x02
COMMAND_GLITCH = 0x03

class EMFDevice(gatt.Device):
    def __init__(self, mac_address, manager, connect_callback) -> Self:
        super().__init__(mac_address=mac_address, manager=manager)
        self.is_connected = False
        self.command_characteristic = None
        self.connect_callback = connect_callback

    def connect_succeeded(self):
        super().connect_succeeded()
        print("[%s] Connected" % (self.mac_address))
        self.is_connected = True

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.mac_address))
        self.is_connected = False

    def services_resolved(self):
        super().services_resolved()

        print("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            print("[%s]  Service [%s]" % (self.mac_address, service.uuid))
            for characteristic in service.characteristics:
                print("[%s]    Characteristic [%s]" % (self.mac_address, characteristic.uuid))
                if service.uuid == SERVICE_UUID and characteristic.uuid == RECV_CHARACTERISTIC_UUID:
                    print("Discovered command channel!")
                    print(self)
                    self.command_characteristic = characteristic
                    self.connect_callback()

class EMFDriver(ABC):
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def sleep(self):
        pass

    @abstractmethod
    def set_activity(self, level):
        pass

    @abstractmethod
    def glitch(self):
        pass

class BluetoothEMFDriver(EMFDriver):
    def __init__(self):
        self.manager = gatt.DeviceManager(adapter_name='hci0')
        self.device = EMFDevice(
            mac_address=EMF_MAC_ADDRESS, 
            manager=self.manager,
            connect_callback=self._on_connect
        )
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.start()

    def _run_loop(self):
        self.device.connect()
        self.manager.run()

    def _on_connect(self):
        print("Calling reset")
        self.reset()

    def _write_buffer(self, data: list[int]) -> bool:
        arr = bytearray(data)
        if not self.device.command_characteristic:
            return False
        
        self.device.command_characteristic.write_value(arr)
        return True

    def reset(self):
        return self._write_buffer([COMMAND_RESET])
    
    def sleep(self):
        return self._write_buffer([COMMAND_SLEEP])
    
    def set_activity(self, level):
        return self._write_buffer([COMMAND_SET_ACTIVITY, level])
    
    def glitch(self):
        return self._write_buffer([COMMAND_GLITCH])
    
class DummyEMFDriver(EMFDriver):
    def reset(self):
        print("EMF reset called")

    def sleep(self):
        print("EMF sleep called")

    def set_activity(self, level):
        print(f"EMF activity set to {level}")

    def glitch(self):
        print(f"EMF glitch called")
    
def get_emf_driver() -> EMFDriver:
    try:
        return BluetoothEMFDriver()
    except Exception as ex:
        print(f"Failed to initialize bluetooth EMF driver: {ex}")
        print("Falling back to dummy EMF driver")
        return DummyEMFDriver()