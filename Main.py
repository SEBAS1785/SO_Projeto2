import time
import random
import multiprocessing

from configuracao import NUM_PASSENGERS, ARRIVAL_INTERVAL
from registo import AirportLogger
from aeroporto import airport_server
from passageiro import passenger_process


def run_simulation(high_demand: bool = False):
    """
    Simulação completa:
      1. Cria estruturas de dados partilhadas
      2. Lança o processo servidor
      3. Lança os processos passageiro com intervalos de chegada
      4. Aguarda conclusão e imprime o resumo
    """
    manager = multiprocessing.Manager()

    #Estruturas partilhadas
    queue_lock   = multiprocessing.Lock()
    queue_list   = manager.list()        #Fila de embarque (ordenada por prioridade)
    notify_event = multiprocessing.Event()
    result_dict  = manager.dict()        #Resultados por passageiro

    stats_lock   = multiprocessing.Lock()
    stats_dict   = manager.dict({"embarcados": 0, "total_espera": 0.0})

    log_lock     = multiprocessing.Lock()
    stop_event   = multiprocessing.Event()

    logger = AirportLogger(log_lock)

    if high_demand:
        print("Modo ALTA DEMANDA ativado.\n")

    #Processo servidor
    server = multiprocessing.Process(
        target=airport_server,
        args=(
            queue_lock, queue_list, notify_event,
            result_dict, logger,
            stats_lock, stats_dict,
            stop_event,
        ),
        name="Servidor-Aeroporto",
    )
    server.start()

    #Processos passageiro
    passengers = []
    for pid in range(1, NUM_PASSENGERS + 1):
        p = multiprocessing.Process(
            target=passenger_process,
            args=(
                pid, queue_lock, queue_list,
                notify_event, result_dict,
                logger, high_demand,
            ),
            name=f"Passageiro-{pid}",
        )
        passengers.append(p)
        p.start()

        #Intervalo de chegada (mais curto em alta demanda)
        if high_demand:
            time.sleep(random.uniform(0.0, 0.3))
        else:
            time.sleep(random.uniform(ARRIVAL_INTERVAL * 0.5, ARRIVAL_INTERVAL * 1.5))

    #Aguarda todos os passageiros terminarem
    for p in passengers:
        p.join()

    #Sinaliza ao servidor para encerrar
    stop_event.set()
    notify_event.set()   #Acorda o servidor se estiver em wait()
    server.join(timeout=10)
    if server.is_alive():
        server.terminate()

    #Resumo final
    embarcados   = stats_dict.get("embarcados", 0)
    total_espera = stats_dict.get("total_espera", 0.0)
    desistencias = NUM_PASSENGERS - embarcados
    media_espera = (total_espera / embarcados) if embarcados > 0 else 0.0

    logger.resumo(NUM_PASSENGERS, embarcados, desistencias, media_espera)

    manager.shutdown()


def main():
    print("=" * 70)
    print("  SIMULAÇÃO DO SISTEMA DE EMBARQUE DO AEROPORTO")
    print("=" * 70)
    print(f"\nEscolha o modo de simulação:")
    print("  1 - Normal")
    print("  2 - Alta Demanda (muitos passageiros ao mesmo tempo)")
    escolha = input("\nOpção [1/2]: ").strip()

    high_demand = (escolha == "2")
    run_simulation(high_demand=high_demand)

    print(f"\nLog completo guardado em: airport_log.txt")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
