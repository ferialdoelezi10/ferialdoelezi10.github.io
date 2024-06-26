# This file is part of the "Smartville" project.
# Copyright (c) 2024 University of Insubria
# Licensed under the Apache License 2.0.
# SPDX-License-Identifier: Apache-2.0
# For the full text of the license, visit:
# https://www.apache.org/licenses/LICENSE-2.0

# Smartville is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License 2.0 for more details.

# You should have received a copy of the Apache License 2.0
# along with Smartville. If not, see <https://www.apache.org/licenses/LICENSE-2.0>.

# Additional licensing information for third-party dependencies
# used in this file can be found in the accompanying `NOTICE` file.
from confluent_kafka import Consumer, KafkaException
from confluent_kafka.admin import AdminClient
import threading
import math

RAM = 'RAM'
CPU = 'CPU'
IN_TRAFFIC = 'IN_TRAFFIC'
OUT_TRAFFIC = 'OUT_TRAFFIC'
DELAY = 'DELAY'


class ConsumerThread(threading.Thread):


    def __init__(
            self, 
            bootstrap_servers,
            topic_name, 
            topic_object,
            cpu_metric, 
            ram_metric, 
            ping_metric, 
            incoming_traffic_metric,
            outcoming_traffic_metric,
            controller_metrics_dict
            ):
        
        threading.Thread.__init__(self)

        self.lock = threading.Lock()
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = topic_name
        self.topic_object = topic_object
        self.cpu_metric = cpu_metric
        self.ram_metric = ram_metric
        self.ping_metric = ping_metric
        self.incoming_traffic_metric = incoming_traffic_metric
        self.outcoming_traffic_metric = outcoming_traffic_metric
        self.exit_signal = threading.Event()
        self.controller_metrics_dict = controller_metrics_dict


    # Definizione metodi di aggiornamento delle metriche nelle rispettive variabili
    def update_cpu_metric(self, value, label_value):
        self.cpu_metric.labels(label_name=label_value).set(value)
        with self.lock:
            if value == b'nan' or math.isnan(value):
                value = -1.0
            self.controller_metrics_dict[self.topic_name][CPU].append(value)


    def update_ram_metric(self, value, label_value):
        self.ram_metric.labels(label_name=label_value).set(value)
        with self.lock:
            if value == b'nan' or math.isnan(value):
                value = -1.0
            self.controller_metrics_dict[self.topic_name][RAM].append(value)

    def update_ping_metric(self, value, label_value):
        self.ping_metric.labels(label_name=label_value).set(value)
        with self.lock:
            if value == b'nan' or math.isnan(value):
                value = -1.0
            self.controller_metrics_dict[self.topic_name][DELAY].append(value)

    def update_incoming_traffic_metric(self, value, label_value):
        self.incoming_traffic_metric.labels(label_name=label_value).set(value)
        with self.lock:
            if value == b'nan' or math.isnan(value):
                value = -1.0
            self.controller_metrics_dict[self.topic_name][IN_TRAFFIC].append(value)

    def update_outcoming_traffic_metric(self, value, label_value):
        self.outcoming_traffic_metric.labels(label_name=label_value).set(value)
        with self.lock:
            if value == b'nan' or math.isnan(value):
                value = -1.0
            self.controller_metrics_dict[self.topic_name][OUT_TRAFFIC].append(value)

    def stop_threads(self):
        print("Stopping thread...")
        self.exit_signal.set()
    

    def run(self):

        # Definizione metodi di connessione al server Kafka
        consumer_conf = {'bootstrap.servers': self.bootstrap_servers, 
                         'group.id': 'my-group'}
        consumer = Consumer(consumer_conf)

        conf = {'bootstrap.servers': self.bootstrap_servers}
        admin_client = AdminClient(conf)
        
        delete_ok = False
        end_message = str(math.nan).encode('utf-8')
        stopper = 0       

        # Estrazione numero delle partizioni dal topic
        num_partitions = len(self.topic_object.partitions)

        # Controllo se il topic a cui ci si deve iscrivere sia corretto: viene considerata una condizione
        # sufficiente se il numero di partizioni all'interno del topic sono esattamente 5
        if (num_partitions==5):

            consumer.subscribe([self.topic_name])

            try:

                while not self.exit_signal.is_set():

                    # Il messaggio viene atteso per massimo 3 secondi
                    msg = consumer.poll(timeout=3)

                    #print(f'Got message: {msg.value().decode("utf-8")} from partition {msg.partition()}')

                    # Nel caso non arrivasse alcun messaggio, vengono inseriti valori nulli per le 
                    # rispettive metriche

                    if msg is None :
                        self.update_cpu_metric(end_message, self.topic_name)
                        self.update_ram_metric(end_message, self.topic_name)
                        self.update_ping_metric(end_message, self.topic_name)
                        self.update_incoming_traffic_metric(end_message, self.topic_name)
                        self.update_outcoming_traffic_metric(end_message, self.topic_name)

                        stopper += 1

                        # Nel caso non si ricevesse alcun messaggio per 40*3 = 120 secondi, viene interrotto
                        # il ciclo
                        if (stopper <40):
                            continue
                        else:
                            delete_ok = True
                            break

                    if msg.error():
                        if msg.error().code() == KafkaException._PARTITION_EOF:
                            print(f'Partition {msg.partition()} terminated')
                            continue
                        else:
                            print(f'Error: {msg.error()}')
                            break

                    # Lettura metriche dal server: ciascuna metrica ha la propria partizione dedicata
                    # Ciascuna metrica verrà monitorata tramite Prometheus e inserita nel suo sistema di
                    # archiviazione
                    if (msg.partition()==0):
                        # print(f'Valore CPU letto da {self.topic}: {msg.value().decode("utf-8")}')
                        self.update_cpu_metric(float(msg.value()), self.topic_name)
                        stopper = 0

                    elif (msg.partition()==1):
                        # print(f'Valore RAM letto da {self.topic}: {msg.value().decode("utf-8")}')
                        self.update_ram_metric(float(msg.value()), self.topic_name)
                        stopper = 0

                    elif (msg.partition()==2):
                        # print(f'Valore latenza letto da {self.topic}: {msg.value().decode("utf-8")}')
                        self.update_ping_metric(float(msg.value()), self.topic_name)
                        stopper = 0

                    elif (msg.partition()==3):
                        # print(f'Valore traffico rete in entrata letto da {self.topic}: {msg.value().decode("utf-8")}')
                        self.update_incoming_traffic_metric(float(msg.value()), self.topic_name)
                        stopper = 0

                    elif (msg.partition()==4):
                        # print(f'Valore traffico rete in uscita letto da {self.topic}: {msg.value().decode("utf-8")}')
                        self.update_outcoming_traffic_metric(float(msg.value()), self.topic_name)
                        stopper = 0

            # Quando viene interrotto il ciclo, se ciò è dovuto alla mancanza di ricezione dei messaggi
            # per un periodo troppo lungo stabilito dalla variabile booleana "delete_ok", il thread viene 
            # arrestato e il topic dedicatogli viene eliminato in maniera tale da fare pulizia all'interno
            # del server kafka         
            finally:

                if delete_ok:
                    admin_client.delete_topics([self.topic_name])

                print(f"{self.topic_name}: stopped thread")

        else:

            admin_client.delete_topics([self.topic_name])
            print(f"topic {self.topic_name} did not registered correctly")
