# =============================================================================
# config.py - Configurações globais da simulação
# =============================================================================

# Número de portões de embarque disponíveis
NUM_GATES = 3

# Número de agentes de embarque disponíveis
NUM_AGENTS = 4

# Número total de passageiros na simulação
NUM_PASSENGERS = 20

# Tempo máximo de espera antes de desistir (em segundos simulados)
MAX_WAIT_TIME = 15

# Intervalo de chegada entre passageiros (segundos reais)
ARRIVAL_INTERVAL = 0.5

# Duração do embarque por prioridade (segundos reais)
BOARDING_DURATION = {
    "alta":   1.0,
    "média":  1.5,
    "baixa":  2.0,
}

# Mapeamento de classe do bilhete para prioridade
TICKET_PRIORITY = {
    "primeira":   "alta",
    "executiva":  "média",
    "económica":  "baixa",
}

# Ficheiro de log
LOG_FILE = "airport_log.txt"
