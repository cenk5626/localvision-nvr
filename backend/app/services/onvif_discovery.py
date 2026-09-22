"""
LocalVision NVR - ONVIF ve Yerel Ağ Keşif Servisi (WS-Discovery).
Yerel ağdaki ONVIF Profile S/T uyumlu kameraları UDP Multicast (239.255.255.250:3702) ile keşfeder.
"""

import logging
import re
import socket
import time
from typing import Any, Dict, List
import uuid

logger = logging.getLogger(__name__)

# Standart ONVIF WS-Discovery Probe Şablonu
WS_DISCOVERY_PROBE = """<?xml version="1.0" encoding="utf-8"?>
<Envelope xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
          xmlns="http://www.w3.org/2003/05/soap-envelope">
  <Header>
    <wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">uuid:{message_id}</wsa:MessageID>
    <wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    <wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
  </Header>
  <Body>
    <Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
      <Types>tds:Device</Types>
    </Probe>
  </Body>
</Envelope>"""


class OnvifDiscoveryService:
    """Yerel ağdaki ONVIF IP kameraları bulan servis."""

    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 3702

    @classmethod
    def discover_cameras(cls, timeout_seconds: float = 3.0) -> List[Dict[str, Any]]:
        """
        Yerel ağa WS-Discovery probe paketi gönderir ve cevap veren ONVIF cihazları listeler.
        """
        discovered: List[Dict[str, Any]] = []
        message_id = str(uuid.uuid4())
        payload = WS_DISCOVERY_PROBE.format(message_id=message_id).encode("utf-8")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(timeout_seconds)

        try:
            sock.sendto(payload, (cls.MULTICAST_IP, cls.MULTICAST_PORT))
            start_time = time.time()

            seen_ips = set()

            while time.time() - start_time < timeout_seconds:
                try:
                    data, addr = sock.recvfrom(65535)
                    response_text = data.decode("utf-8", errors="ignore")
                    ip_address = addr[0]

                    if ip_address in seen_ips:
                        continue
                    seen_ips.add(ip_address)

                    # XAddrs (Hizmet adresleri) ve Cihaz tipi ayıkla
                    xaddrs_match = re.search(r"<(?:\w+:)?XAddrs>([^<]+)</(?:\w+:)?XAddrs>", response_text)
                    xaddrs = xaddrs_match.group(1).strip() if xaddrs_match else f"http://{ip_address}/onvif/device_service"

                    # Port ayıkla
                    port = 80
                    port_match = re.search(r":(\d+)/", xaddrs)
                    if port_match:
                        port = int(port_match.group(1))

                    discovered.append({
                        "ip": ip_address,
                        "port": port,
                        "xaddrs": xaddrs,
                        "manufacturer": "ONVIF Uyumlu Kamera",
                        "model": "Profile S/T",
                        "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Discovery paket okuma hatası: {e}")

        except Exception as e:
            logger.warning(f"ONVIF keşif hatası (Yerel ağ kısıtı olabilir): {e}")
        finally:
            sock.close()

        return discovered


onvif_service = OnvifDiscoveryService()
