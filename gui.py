import os
import json
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from main import run_simulation

LOG_FILE = "airport_log.txt"
STATS_FILE = "stats.json"


class AirportGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simulação de Embarque - Aeroporto")

        # Estado
        self.simulation_thread = None
        self.simulation_running = False
        self._last_running_state = False
        self.last_log_size = 0

        # Layout
        self._build_widgets()

        # Começa a atualizar a área de log periodicamente
        self._schedule_log_update()

    def _build_widgets(self):
        # Frame de controlos (botões)
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_normal = tk.Button(
            control_frame,
            text="Simulação Normal",
            command=lambda: self.start_simulation(high_demand=False),
            width=18,
        )
        self.btn_normal.pack(side=tk.LEFT, padx=5)

        self.btn_high = tk.Button(
            control_frame,
            text="Alta Demanda",
            command=lambda: self.start_simulation(high_demand=True),
            width=18,
        )
        self.btn_high.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(
            control_frame,
            text="Fechar",
            command=self.on_close,
            width=10,
        )
        self.btn_stop.pack(side=tk.RIGHT, padx=5)

        # Área de log (scrolled text)
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        lbl = tk.Label(log_frame, text="Log do sistema de embarque:")
        lbl.pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=25,
            state=tk.DISABLED,
            font=("Consolas", 9),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def start_simulation(self, high_demand: bool):
        if self.simulation_running:
            messagebox.showinfo(
                "Simulação em curso",
                "Já existe uma simulação a correr. Aguarda terminar."
            )
            return

        # Limpa o ficheiro de log anterior
        try:
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
        except OSError:
            pass

        # Limpa ficheiro de stats anterior (se existir)
        try:
            if os.path.exists(STATS_FILE):
                os.remove(STATS_FILE)
        except OSError:
            pass

        # Limpa a área de texto
        self._clear_log_view()
        self.last_log_size = 0

        # Arranca a simulação numa thread para não bloquear a GUI
        self.simulation_running = True
        self._last_running_state = True
        self.simulation_thread = threading.Thread(
            target=self._run_simulation_wrapper,
            args=(high_demand,),
            daemon=True,
        )
        self.simulation_thread.start()

    def _run_simulation_wrapper(self, high_demand: bool):
        try:
            run_simulation(high_demand=high_demand)
        except Exception as e:
            # Em caso de erro, mostra uma mensagem
            messagebox.showerror("Erro na simulação", str(e))
        finally:
            # Marca que terminou
            self.simulation_running = False

    def _schedule_log_update(self):
        # Agenda actualização do log a cada 300 ms
        self.root.after(300, self._update_log_view)

    def _update_log_view(self):
        """
        Lê o ficheiro de log e acrescenta novas linhas à área de texto,
        sem bloquear a interface.
        """
        if os.path.exists(LOG_FILE):
            try:
                current_size = os.path.getsize(LOG_FILE)
                if current_size > self.last_log_size:
                    # Há novas linhas para ler
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        f.seek(self.last_log_size)
                        new_data = f.read()
                        if new_data:
                            self._append_log_text(new_data)
                    self.last_log_size = current_size
            except OSError:
                # Se houver algum problema de I/O, ignora neste tick
                pass

        # Verificar se a simulação acabou agora
        if self._last_running_state and not self.simulation_running:
            # Acabou de terminar → tentar mostrar gráfico
            self._show_stats_chart()
        self._last_running_state = self.simulation_running

        # Volta a agendar
        self._schedule_log_update()

    def _append_log_text(self, text: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log_view(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _show_stats_chart(self):
        """
        Lê stats.json (gerado no fim da simulação) e mostra
        uma janela com gráfico de barras e resumo textual.
        """
        if not os.path.exists(STATS_FILE):
            return

        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            return

        total = stats.get("total", 0)
        embarcados = stats.get("embarcados", 0)
        desistencias = stats.get("desistencias", 0)
        media_espera = stats.get("media_espera", 0.0)

        # Janela nova para o gráfico
        win = tk.Toplevel(self.root)
        win.title("Resumo Estatístico da Simulação")

        # Label com resumo
        info = (
            f"Total: {total} | Embarcados: {embarcados} | "
            f"Desistências: {desistencias} | Tempo médio de espera: {media_espera:.1f}s"
        )
        lbl = tk.Label(win, text=info)
        lbl.pack(pady=5)

        # Figura matplotlib
        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        categorias = ["Embarcados", "Desistências"]
        valores = [embarcados, desistencias]
        cores = ["green", "red"]

        ax.bar(categorias, valores, color=cores)
        ax.set_ylabel("Número de passageiros")
        ax.set_title("Resultados da Simulação")

        # Embutir figura em Tkinter
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Botão fechar
        btn_close = tk.Button(win, text="Fechar", command=win.destroy)
        btn_close.pack(pady=5)

    def on_close(self):
        if self.simulation_running:
            if not messagebox.askyesno(
                "Fechar",
                "Uma simulação ainda está a correr. Tens a certeza que queres sair?"
            ):
                return

        # Pequeno tempo para a thread terminar de forma limpa
        time.sleep(0.2)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AirportGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()