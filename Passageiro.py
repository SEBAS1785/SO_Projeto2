# =============================================================================
# passenger.py - Processo Passageiro (Cliente)
# =============================================================================

import time
import random
import multiprocessing
from dataclasses import dataclass, field
from typing import Optional
from configuracao import TICKET_PRIORITY, BOARDING_DURATION, MAX_WAIT_TIME


# Mapeamento de prioridade para valor numérico (menor = maior prioridade)
PRIORITY_VALUE = {"alta": 0, "média": 1, "baixa": 2}

# Nomes e apelidos para gerar passageiros aleatórios
NOMES = ["Ana", "Bruno", "Carla", "David", "Eva", "Fábio", "Gisela",
         "Hugo", "Inês", "João", "Kátia", "Luís", "Maria", "Nuno",
         "Olga", "Paulo", "Rana", "Sara", "Tiago", "Vera"]


@dataclass
class PassengerData:
    """
    Estrutura de dados que representa um passageiro.
    Usada na fila partilhada entre processos.
    """
    pid: int
    nome: str
    classe: str
    prioridade: str
    prioridade_val: int          # valor numérico para ordenação
    hora_chegada: float          # timestamp de chegada
    hora_embarque: Optional[float] = None
    tempo_espera: Optional[float] = None
    desistiu: bool = False

    def __lt__(self, other):
        """Ordenação: primeiro por prioridade, depois por hora de chegada (FIFO)."""
        if self.prioridade_val != other.prioridade_val:
            return self.prioridade_val < other.prioridade_val
        return self.hora_chegada < other.hora_chegada


def gerar_passageiro(pid: int) -> PassengerData:
    """Cria um passageiro com atributos aleatórios."""
    nome = random.choice(NOMES) + f"_{pid}"
    classe = random.choice(list(TICKET_PRIORITY.keys()))
    prioridade = TICKET_PRIORITY[classe]
    return PassengerData(
        pid=pid,
        nome=nome,
        classe=classe,
        prioridade=prioridade,
        prioridade_val=PRIORITY_VALUE[prioridade],
        hora_chegada=time.time(),
    )


def passenger_process(
    pid: int,
    queue_lock: multiprocessing.Lock,
    queue_list,          # multiprocessing.Manager().list()
    notify_event: multiprocessing.Event,
    result_dict,         # multiprocessing.Manager().dict()
    logger,
    high_demand: bool = False,
):
    """
    Função principal do processo passageiro.

    Fluxo:
      1. Gera os dados do passageiro
      2. Regista chegada no log
      3. Insere-se na fila partilhada (com lock)
      4. Notifica o servidor
      5. Aguarda resposta (embarque ou timeout → desistência)
    """
    passageiro = gerar_passageiro(pid)

    # Simula chegada com pequeno atraso aleatório em alta demanda
    if high_demand:
        time.sleep(random.uniform(0, 0.2))

    # --- Regista chegada ---
    logger.chegada(pid, passageiro.nome, passageiro.classe, passageiro.prioridade)

    # --- Insere na fila partilhada ordenada por prioridade ---
    with queue_lock:
        queue_list.append(passageiro)
        # Ordena a lista partilhada mantendo a prioridade
        ordenada = sorted(list(queue_list))
        del queue_list[:]
        queue_list.extend(ordenada)
        pos = list(queue_list).index(passageiro) + 1
    logger.fila(passageiro.nome, pos)

    # Notifica o servidor que há um novo passageiro
    notify_event.set()

    # --- Aguarda resultado (embarque ou desistência) ---
    inicio_espera = time.time()
    while True:
        time.sleep(0.2)
        espera = time.time() - inicio_espera

        # Verifica se o servidor já processou este passageiro
        if passageiro.nome in result_dict:
            resultado = result_dict[passageiro.nome]
            if resultado.get("desistiu"):
                logger.desistencia(passageiro.nome, espera)
            return

        # Timeout: passageiro desiste
        if espera >= MAX_WAIT_TIME:
            with queue_lock:
                # Remove da fila se ainda estiver lá
                atual = list(queue_list)
                nova = [p for p in atual if p.nome != passageiro.nome]
                del queue_list[:]
                queue_list.extend(nova)
            result_dict[passageiro.nome] = {"desistiu": True, "espera": espera}
            logger.desistencia(passageiro.nome, espera)
            return
