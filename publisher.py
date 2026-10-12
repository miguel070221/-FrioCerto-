"""AF12 FrioCerto: 14 sensores IoT simulados.

Parte A: MQTT 5, leituras QoS 1, alertas QoS 2.
Topico: friocerto/<regiao>/<cidade>/<loja>/<camara>/<tipo>
InfluxDB: temperatura_camara [temp_c, umid_pct] e alerta_evento.
Em produção, conectividade NB-IoT e buffer local seriam necessários.
"""
import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

LOJAS = [
    ("santo-andre", "sa-01"),
    ("santo-andre", "sa-02"),
    ("santo-andre", "sa-03"),
    ("santo-andre", "sa-04"),
    ("sao-bernardo", "sbc-01"),
    ("sao-bernardo", "sbc-02"),
    ("sao-bernardo", "sbc-03"),
    ("sao-bernardo", "sbc-04"),
    ("sao-caetano", "scs-01"),
    ("sao-caetano", "scs-02"),
    ("sao-caetano", "scs-03"),
    ("diadema", "dia-01"),
    ("diadema", "dia-02"),
    ("diadema", "dia-03"),
]

INTERVALO = float(os.getenv("INTERVALO_SEGUNDOS", "2"))  # produção: 60
ANOMALIA_APOS = float(os.getenv("ANOMALIA_APOS_SEGUNDOS", "20"))
DURACAO_ALERTA = 300  # exigido: acima do limite por 5 minutos
LOJA_ANORMAL = "sbc-02"


def utc_agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def publicar(cliente, topico, registro, qos):
    resposta = cliente.publish(topico, json.dumps(registro, ensure_ascii=False), qos=qos)
    if resposta.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(f"Falha na publicação em {topico}: {resposta.rc}")


def main():
    cliente = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="friocerto-publisher-14-lojas",
        protocol=mqtt.MQTTv5,
    )
    for tentativa in range(1, 31):
        try:
            cliente.connect("127.0.0.1", 1883, keepalive=60)
            break
        except OSError as erro:
            if tentativa == 30:
                raise
            print(f"Broker não pronto ({erro}); tentativa {tentativa}/30", flush=True)
            time.sleep(2)
    cliente.loop_start()
    inicio = time.monotonic()
    inicio_anomalia = None
    alerta_enviado = False
    print(f"Publicando {len(LOJAS)} sensores a cada {INTERVALO}s", flush=True)

    try:
        while True:
            agora = time.monotonic()
            if inicio_anomalia is None and agora - inicio >= ANOMALIA_APOS:
                inicio_anomalia = agora
                print("ANOMALIA INICIADA: loja sbc-02 com 12,4 °C", flush=True)

            for cidade, loja in LOJAS:
                anormal = loja == LOJA_ANORMAL and inicio_anomalia is not None
                temperatura = 12.4 if anormal else round(random.uniform(3, 7), 2)
                umidade = round(random.uniform(40, 65), 2)
                raiz = f"friocerto/abc/{cidade}/{loja}/camara01"
                dados = {
                    "regiao": "abc",
                    "cidade": cidade,
                    "loja": loja,
                    "camara": "camara01",
                    "temp_c": temperatura,
                    "umid_pct": umidade,
                    "ts": utc_agora(),
                }
                publicar(cliente, f"{raiz}/leitura", dados, qos=1)
                print(f"{loja}: {temperatura:.2f} °C", flush=True)

                if (anormal and not alerta_enviado
                        and agora - inicio_anomalia >= DURACAO_ALERTA):
                    evento = {
                        **dados,
                        "duracao_min": 5,
                        "temp_max": temperatura,
                        "intervencao": False,
                        "falso_positivo": False,
                    }
                    publicar(cliente, f"{raiz}/alerta", evento, qos=2)
                    alerta_enviado = True
                    print("ALERTA MQTT QoS 2: sbc-02 >8 °C há 5 min", flush=True)

            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print("Simulação encerrada.", flush=True)
    finally:
        cliente.disconnect()
        cliente.loop_stop()


if __name__ == "__main__":
    main()
