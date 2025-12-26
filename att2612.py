import customtkinter as ctk
from tinydb import TinyDB, Query
import random
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter.messagebox as messagebox  # Para exibir erros de forma amigável

# ================= CONFIG =================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ================= BANCO =================
db = TinyDB("db.json")
produtos = db.table("produtos")
posicoes = db.table("posicoes")
pedidos = db.table("pedidos")
Q = Query()

# ================= UTIL =================
def gerar_codigo(tabela, campo="sku"):
    """Gera um código único de 6 dígitos"""
    while True:
        codigo = str(random.randint(1, 999999)).zfill(6)
        if not tabela.search(Q[campo] == codigo):
            return codigo

def limpar(frame):
    """Limpa todos os widgets de um frame"""
    for widget in frame.winfo_children():
        widget.destroy()

# ================= GRAFICOS =================
def grafico_pedidos(frame):
    atendidos = len(pedidos.search(Q.status == "EXPEDIDO"))
    total = len(pedidos.all())
    pendentes = total - atendidos

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        [atendidos, pendentes],
        labels=["Atendidos", "Pendentes"],
        autopct="%1.0f%%",
        startangle=90,
        colors=["#4CAF50", "#F44336"]
    )
    ax.set_title("Status dos Pedidos")
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="left", padx=40, fill="both", expand=True)

def grafico_ocupacao(frame):
    total_pos = len(posicoes.all())
    ocupadas = len({p["posicao"] for p in produtos.all() if p.get("posicao") and p.get("quantidade", 0) > 0})
    livres = total_pos - ocupadas

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        [ocupadas, livres],
        labels=["Ocupadas", "Livres"],
        autopct="%1.0f%%",
        startangle=90,
        colors=["#2196F3", "#9E9E9E"]
    )
    ax.set_title("Ocupação do Armazém")
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="right", padx=40, fill="both", expand=True)

# ================= POSIÇÕES =================
def criar_posicoes_em_lote(deposito, letra_ini, letra_fim, prateleiras, niveis):
    letras = string.ascii_uppercase
    try:
        ini_idx = letras.index(letra_ini.upper())
        fim_idx = letras.index(letra_fim.upper())
    except ValueError:
        messagebox.showerror("Erro", "Letras inicial ou final inválidas (use A-Z)")
        return

    for l in letras[ini_idx : fim_idx + 1]:
        for p in range(1, prateleiras + 1):
            for n in range(1, niveis + 1):
                codigo = f"{deposito}-{l}-{p:02d}-{n:02d}"  # formato mais bonito: 01, 02...
                if not posicoes.search(Q.codigo == codigo):
                    posicoes.insert({"codigo": codigo})

# ================= APP =================
app = ctk.CTk()
app.geometry("1400x820")
app.title("Maur WMS")

sidebar = ctk.CTkFrame(app, width=240, corner_radius=0)
sidebar.pack(side="left", fill="y")

content = ctk.CTkFrame(app)
content.pack(expand=True, fill="both", padx=20, pady=20)

main = ctk.CTkFrame(content, corner_radius=16)
main.pack(expand=True, fill="both")

ctk.CTkLabel(
    sidebar,
    text="Maur WMS",
    font=ctk.CTkFont(size=22, weight="bold")
).pack(pady=30)

# ================= DASHBOARD =================
def tela_dashboard():
    limpar(main)
    ctk.CTkLabel(main, text="Dashboard", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    info = ctk.CTkFrame(main)
    info.pack(pady=10)
    ctk.CTkLabel(info, text=f"Total de Posições: {len(posicoes.all())}").pack(anchor="w")
    ctk.CTkLabel(info, text=f"Total de Pedidos: {len(pedidos.all())}").pack(anchor="w")

    graficos = ctk.CTkFrame(main)
    graficos.pack(expand=True, fill="both", pady=20)
    grafico_pedidos(graficos)
    grafico_ocupacao(graficos)

# ================= PRODUTOS =================
def tela_produtos():
    limpar(main)
    ctk.CTkLabel(main, text="Cadastro de Produtos", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    frame_form = ctk.CTkFrame(main)
    frame_form.pack(pady=20, padx=80)

    nome = ctk.CTkEntry(frame_form, placeholder_text="Nome do produto", width=400)
    pos = ctk.CTkEntry(frame_form, placeholder_text="Posição (ex: A-01-01)", width=400)
    qtd = ctk.CTkEntry(frame_form, placeholder_text="Quantidade", width=400)

    for e in (nome, pos, qtd):
        e.pack(fill="x", pady=8)

    def salvar():
        try:
            qtd_val = int(qtd.get())
            if qtd_val < 0:
                raise ValueError("Quantidade não pode ser negativa")
            pos_val = pos.get().strip().upper()
            if not pos_val:
                raise ValueError("Posição é obrigatória")

            produtos.insert({
                "sku": gerar_codigo(produtos, "sku"),
                "nome": nome.get().strip(),
                "quantidade": qtd_val,
                "posicao": pos_val
            })
            messagebox.showinfo("Sucesso", "Produto cadastrado!")
            nome.delete(0, "end")
            pos.delete(0, "end")
            qtd.delete(0, "end")
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e))

    ctk.CTkButton(main, text="Cadastrar Produto", command=salvar, width=200).pack(pady=20)

# ================= CONSULTA =================
def tela_consulta():
    limpar(main)
    ctk.CTkLabel(main, text="Consulta de Produtos", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    entrada = ctk.CTkEntry(main, placeholder_text="Digite SKU ou parte do Nome", width=400)
    entrada.pack(pady=10, padx=80)

    box = ctk.CTkTextbox(main, width=800, height=400)
    box.pack(expand=True, fill="both", padx=80, pady=10)

    def buscar():
        box.delete("1.0", "end")
        termo = entrada.get().strip().lower()
        if not termo:
            box.insert("end", "Digite algo para buscar...\n")
            return

        encontrados = 0
        for p in produtos.all():
            if termo in p.get("nome", "").lower() or termo == p.get("sku", ""):
                box.insert(
                    "end",
                    f"{p['sku']} | {p['nome']} | Qtd: {p['quantidade']} | Pos: {p.get('posicao', '—')}\n"
                )
                encontrados += 1
        if encontrados == 0:
            box.insert("end", "Nenhum produto encontrado.\n")

    ctk.CTkButton(main, text="Pesquisar", command=buscar, width=200).pack(pady=10)

# ================= POSIÇÕES =================
def tela_posicoes():
    limpar(main)
    ctk.CTkLabel(main, text="Gerenciamento de Posições", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    ctk.CTkButton(main, text="Criar Posições em Lote", command=tela_criar_lote).pack(pady=10)

    # Área com scroll
    canvas = ctk.CTkCanvas(main, highlightthickness=0)
    scroll = ctk.CTkScrollbar(main, orientation="vertical", command=canvas.yview)
    frame = ctk.CTkFrame(canvas)

    frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    col = row = 0
    for pos in posicoes.all():
        codigo = pos["codigo"]
        card = ctk.CTkFrame(frame, width=240, height=140, corner_radius=16)
        card.grid(row=row, column=col, padx=15, pady=15)
        card.grid_propagate(False)

        def on_click(event, cod=codigo):
            abrir_posicao(cod)

        card.bind("<Button-1>", on_click)

        lbl = ctk.CTkLabel(
            card,
            text=codigo,
            font=ctk.CTkFont(size=16, weight="bold"),
            cursor="hand2"
        )
        lbl.pack(expand=True)
        lbl.bind("<Button-1>", on_click)

        col += 1
        if col == 5:  # 5 colunas
            col = 0
            row += 1

def abrir_posicao(codigo):
    limpar(main)
    ctk.CTkLabel(main, text=f"Detalhes da Posição {codigo}", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    box = ctk.CTkTextbox(main, width=800, height=400)
    box.pack(expand=True, fill="both", padx=80, pady=20)

    itens = produtos.search(Q.posicao == codigo)
    itens_validos = [p for p in itens if p.get("quantidade", 0) > 0]

    if not itens_validos:
        box.insert("end", "Esta posição está vazia no momento.\n")
    else:
        for p in itens_validos:
            box.insert("end", f"{p['sku']} | {p['nome']} | Qtd: {p['quantidade']}\n")

    ctk.CTkButton(main, text="Voltar", command=tela_posicoes).pack(pady=10)

# ================= CRIAR POSIÇÕES =================
def tela_criar_lote():
    limpar(main)
    ctk.CTkLabel(main, text="Criar Posições em Lote", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

    frame_form = ctk.CTkFrame(main)
    frame_form.pack(pady=20, padx=80)

    d = ctk.CTkEntry(frame_form, placeholder_text="Depósito (ex: 01)", width=400)
    li = ctk.CTkEntry(frame_form, placeholder_text="Letra Inicial (A)", width=400)
    lf = ctk.CTkEntry(frame_form, placeholder_text="Letra Final (Z)", width=400)
    p = ctk.CTkEntry(frame_form, placeholder_text="Número de Prateleiras", width=400)
    n = ctk.CTkEntry(frame_form, placeholder_text="Número de Níveis", width=400)

    for e in (d, li, lf, p, n):
        e.pack(fill="x", pady=8)

    def gerar():
        try:
            dep = int(d.get())
            pr = int(p.get())
            ni = int(n.get())
            if pr <= 0 or ni <= 0:
                raise ValueError("Prateleiras e níveis devem ser maiores que 0")

            criar_posicoes_em_lote(dep, li.get(), lf.get(), pr, ni)
            messagebox.showinfo("Sucesso", "Posições criadas!")
            tela_posicoes()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
        except Exception as e:
            messagebox.showerror("Erro inesperado", str(e))

    ctk.CTkButton(main, text="Gerar Posições", command=gerar, width=200).pack(pady=20)

# ================= MENU LATERAL =================
def menu_btn(txt, cmd):
    btn = ctk.CTkButton(
        sidebar,
        text=txt,
        height=50,
        corner_radius=10,
        command=cmd
    )
    btn.pack(fill="x", padx=20, pady=6)

menu_btn("Dashboard", tela_dashboard)
menu_btn("Produtos", tela_produtos)
menu_btn("Consulta", tela_consulta)
menu_btn("Posições", tela_posicoes)

# ================= START =================
tela_dashboard()
app.mainloop()
