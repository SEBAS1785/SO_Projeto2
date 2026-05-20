import time
import multiprocessing
from configuracao import NUM_GATES, NUM_AGENTS, BOARDING_DURATION

def boarding_worker(
    passageiro,
    gate_id: int,
    agent_id: int,
    gate_semaphore: multiprocessing.Semaphore,
    agent_semaphore: multiprocessing.Semaphore,
    result_dict,
    logger,
    stats_lock: multiprocessing.Lock,
    stats_dict,
):
    """
    Processo/thread que realiza o embarque de um único passageiro
    Ocupa um portão e um agente enquanto o embarque decorre
    """
    hora_embarque = time.time()
    espera = hora_embarque - passageiro.hora_chegada

    logger.embarque_inicio(passageiro.nome, gate_id, agent_id, espera)

    #Simula o tempo de embarque conforme a prioridade
    duracao = BOARDING_DURATION[passageiro.prioridade]
    time.sleep(duracao)

    logger.embarque_fim(passageiro.nome, gate_id, duracao)

    #Regista o resultado para o processo passageiro verificar
    result_dict[passageiro.nome] = {
        "desistiu": False,
        "espera": espera,
        "duracao": duracao,
        "portao": gate_id,
        "agente": agent_id,
    }

    #Atualiza estatísticas globais
    with stats_lock:
        stats_dict["embarcados"] = stats_dict.get("embarcados", 0) + 1
        total_espera = stats_dict.get("total_espera", 0.0) + espera
        stats_dict["total_espera"] = total_espera

    #Liberta os recursos (semáforos)
    gate_semaphore.release()
    agent_semaphore.release()


def airport_server(
    queue_lock: multiprocessing.Lock,
    queue_list,
    notify_event: multiprocessing.Event,
    result_dict,
    logger,
    stats_lock: multiprocessing.Lock,
    stats_dict,
    stop_event: multiprocessing.Event,
):
    """
    Processo servidor principal do aeroporto.

    Responsabilidades:
      - Monitoriza a fila de embarque continuamente
      - Aloca portões e agentes disponíveis (semáforos)
      - Lança um processo de embarque para cada passageiro atendido
      - Para quando recebe o sinal de paragem (stop_event)
    """
    #Semáforos que limitam o acesso concorrente aos recursos
    gate_semaphore  = multiprocessing.Semaphore(NUM_GATES)
    agent_semaphore = multiprocessing.Semaphore(NUM_AGENTS)

    #Controlo dos IDs dos portões e dos agentes em uso
    gate_manager  = multiprocessing.Manager()
    gates_in_use  = gate_manager.list(range(1, NUM_GATES + 1))   # IDs livres
    agents_in_use = gate_manager.list(range(1, NUM_AGENTS + 1))  # IDs livres
    resource_lock = multiprocessing.Lock()

    active_workers = []

    print("\n✈  Servidor do aeroporto iniciado. A aguardar passageiros...\n")

    while not stop_event.is_set():
        #Aguarda notificação ou verifica a cada 0.3s
        notify_event.wait(timeout=0.3)
        notify_event.clear()

        #Processa todos os passageiros que conseguir com recursos disponíveis
        while True:
            passageiro = None

            #Tenta obter o próximo passageiro da fila
            with queue_lock:
                if len(queue_list) > 0:
                    passageiro = queue_list[0]
                    #Verifica se o passageiro já desistiu entretanto
                    if passageiro.nome in result_dict and result_dict[passageiro.nome].get("desistiu"):
                        del queue_list[0]
                        passageiro = None
                        continue

            if passageiro is None:
                break

            #Tenta adquirir portão e agente
            got_gate  = gate_semaphore.acquire(block=False)
            if not got_gate:
                break  # Sem portões livres, aguarda

            got_agent = agent_semaphore.acquire(block=False)
            if not got_agent:
                gate_semaphore.release()
                break  #Sem agentes livres aguarda

            #Remove o passageiro da fila
            with queue_lock:
                if len(queue_list) > 0 and queue_list[0].nome == passageiro.nome:
                    del queue_list[0]
                else:
                    #Passageiro já foi removido (desistência), devolve recursos
                    gate_semaphore.release()
                    agent_semaphore.release()
                    continue

            #Atribui IDs de portão e agente
            with resource_lock:
                gate_id  = gates_in_use.pop(0)
                agent_id = agents_in_use.pop(0)

            #Lança processo de embarque
            worker = multiprocessing.Process(
                target=_boarding_and_release,
                args=(
                    passageiro, gate_id, agent_id,
                    gate_semaphore, agent_semaphore,
                    gates_in_use, agents_in_use, resource_lock,
                    result_dict, logger, stats_lock, stats_dict,
                ),
                daemon=True,
            )
            worker.start()
            active_workers.append(worker)

        #Limpa processos já terminados da lista
        active_workers = [w for w in active_workers if w.is_alive()]

    #Aguarda que todos os embarques ativos terminem
    for w in active_workers:
        w.join()

    print("\n✈  Servidor do aeroporto encerrado.")


def _boarding_and_release(
    passageiro,
    gate_id, agent_id,
    gate_semaphore, agent_semaphore,
    gates_in_use, agents_in_use, resource_lock,
    result_dict, logger, stats_lock, stats_dict,
):
    """
    Wrapper que executa o embarque e depois devolve os IDs de portão/agente
    à pool de recursos disponíveis.
    """
    hora_embarque = time.time()
    espera = hora_embarque - passageiro.hora_chegada

    logger.embarque_inicio(passageiro.nome, gate_id, agent_id, espera)

    duracao = BOARDING_DURATION[passageiro.prioridade]
    time.sleep(duracao)

    logger.embarque_fim(passageiro.nome, gate_id, duracao)

    result_dict[passageiro.nome] = {
        "desistiu": False,
        "espera": espera,
        "duracao": duracao,
        "portao": gate_id,
        "agente": agent_id,
    }

    #Atualiza estatísticas
    with stats_lock:
        stats_dict["embarcados"] = stats_dict.get("embarcados", 0) + 1
        stats_dict["total_espera"] = stats_dict.get("total_espera", 0.0) + espera

    #Devolve IDs à pool
    with resource_lock:
        gates_in_use.append(gate_id)
        agents_in_use.append(agent_id)

    #Liberta semáforos
    gate_semaphore.release()
    agent_semaphore.release()
