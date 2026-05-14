# =============================================================================
# logger.py - Registo de operações do aeroporto
# =============================================================================

import os
import multiprocessing
from datetime import datetime
from configuracao import LOG_FILE


class AirportLogger:
    """
    Logger thread-safe para registar todas as operações do aeroporto.
    Usa um Lock para evitar escrita simultânea no ficheiro.
    """

    def __init__(self, lock: multiprocessing.Lock):
        self.lock = lock
        # Cria/limpa o ficheiro de log no início da simulação
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"  LOG DO SISTEMA DE EMBARQUE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

    def _write(self, message: str):
        """Escreve uma linha no log com timestamp, de forma segura."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] {message}\n"
        with self.lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
            # Também imprime na consola
            print(line, end="")

    def chegada(self, pid: int, nome: str, classe: str, prioridade: str):
        self._write(f"CHEGADA    | Passageiro {nome} (PID={pid}) | Classe: {classe:10s} | Prioridade: {prioridade}")

    def fila(self, nome: str, pos: int):
        self._write(f"FILA       | Passageiro {nome} entrou na fila | Posição estimada: {pos}")

    def embarque_inicio(self, nome: str, portao: int, agente: int, espera: float):
        self._write(
            f"EMBARQUE   | Passageiro {nome} | Portão {portao} | Agente {agente} | "
            f"Espera: {espera:.1f}s"
        )

    def embarque_fim(self, nome: str, portao: int, duracao: float):
        self._write(f"CONCLUÍDO  | Passageiro {nome} embarcou | Portão {portao} | Duração: {duracao:.1f}s")

    def desistencia(self, nome: str, espera: float):
        self._write(f"DESISTÊNCIA| Passageiro {nome} desistiu após {espera:.1f}s de espera")

    def resumo(self, total: int, embarcados: int, desistencias: int, tempo_medio: float):
        """Escreve o resumo final da simulação no log."""
        with self.lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 70 + "\n")
                f.write("  RESUMO FINAL DA SIMULAÇÃO\n")
                f.write("=" * 70 + "\n")
                f.write(f"  Total de passageiros  : {total}\n")
                f.write(f"  Embarcados com sucesso: {embarcados}\n")
                f.write(f"  Desistências          : {desistencias}\n")
                f.write(f"  Tempo médio de espera : {tempo_medio:.1f}s\n")
                f.write("=" * 70 + "\n")
        print("\n" + "=" * 70)
        print("  RESUMO FINAL DA SIMULAÇÃO")
        print("=" * 70)
        print(f"  Total de passageiros  : {total}")
        print(f"  Embarcados com sucesso: {embarcados}")
        print(f"  Desistências          : {desistencias}")
        print(f"  Tempo médio de espera : {tempo_medio:.1f}s")
        print("=" * 70)
