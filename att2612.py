import customtkinter as ctk
from tinydb import TinyDB, Query
import random
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
def gerar_codigo(tabela, campo):
    while True:
        codigo = str(random.randint(1, 999999)).zfill(6)
        if not tabela.search(Q[campo] == codigo):
            return codigo

def limpar(frame):
    for w in frame.winfo_children():
        w.destroy()

# ================= GRAFICOS =================
def grafico_pedidos(frame):
    atendidos = len(pedidos.search(Q.status == "EXPEDIDO"))
    pendentes = len(pedidos) - atendidos

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        [atendidos, pendentes],
        labels=["Atendidos", "Pendentes"],
        autopct="%1.0f%%",
        startangle=90
    )
    ax.set_title("Pedidos")

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="left", padx=40)

def grafico_ocupacao(frame):
    total = len(posicoes)
    ocupadas = len({
        p.get("posicao")
        for p in produtos
        if p.get("posicao") and p["quantidade"] > 0
    })
    livres = total - ocupadas

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        [ocupadas, livres],
        labels=["Ocupadas", "Livres"],
        autopct="%1.0f%%",
        startangle=90
    )
    ax.set_title("Armazém")

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="right", padx=40)

# ================= POSIÇÕES =================
def criar_posicoes_em_lote(deposito, letra_ini, letra_fim, prateleiras, niveis):
    letras = string.ascii_uppercase
    for l in letras[letras.index(letra_ini):letras.index(letra_fim) + 1]:
        for p in range(1, prateleiras + 1):
            for n in range(1, niveis + 1):
                codigo = f"{deposito}-{l}-{p}-{n}"
                if not posicoes.search(Q.codigo == codigo):
                    posicoes.insert({"codigo": codigo})

# ================= APP =================
app = ctk.CTk()
app.geometry("1400x820")
app.title("Maur WMS")

sidebar = ctk.CTkFrame(app, width=240)
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

    ctk.CTkLabel(
        main,
        text="Dashboard",
        font=ctk.CTkFont(size=26, weight="bold")
    ).pack(pady=20)

    info = ctk.CTkFrame(main)
    info.pack(pady=10)

    ctk.CTkLabel(info, text=f"Total de Posições: {len(posicoes)}").pack()
    ctk.CTkLabel(info, text=f"Total de Pedidos: {len(pedidos)}").pack()

    graficos = ctk.CTkFrame(main)
    graficos.pack(expand=True, fill="both", pady=20)

    grafico_pedidos(graficos)
    grafico_ocupacao(graficos)

# ================= PRODUTOS =================
def tela_produtos():
    limpar(main)

    ctk.CTkLabel(main, text="Produtos", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

    nome = ctk.CTkEntry(main, placeholder_text="Nome")
    pos = ctk.CTkEntry(main, placeholder_text="Posição")
    qtd = ctk.CTkEntry(main, placeholder_text="Quantidade")

    for e in (nome, pos, qtd):
        e.pack(fill="x", padx=80, pady=6)

    def salvar():
        produtos.insert({
            "sku": gerar_codigo(produtos, "sku"),
            "nome": nome.get(),
            "quantidade": int(qtd.get()),
            "posicao": pos.get().upper()
        })
        tela_produtos()

    ctk.CTkButton(main, text="Cadastrar", command=salvar).pack(pady=10)

# ================= CONSULTA =================
def tela_consulta():
    limpar(main)

    ctk.CTkLabel(main, text="Consulta", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

    entrada = ctk.CTkEntry(main, placeholder_text="SKU ou Nome")
    entrada.pack(fill="x", padx=80, pady=10)

    box = ctk.CTkTextbox(main)
    box.pack(expand=True, fill="both", padx=80, pady=10)

    def buscar():
        box.delete("1.0", "end")
        termo = entrada.get().lower()

        for p in produtos:
            if termo in p["nome"].lower() or termo == p["sku"]:
                box.insert("end", f"{p['sku']} | {p['nome']} | {p['quantidade']} | {p['posicao']}\n")

    ctk.CTkButton(main, text="Pesquisar", command=buscar).pack(pady=10)

# ================= POSIÇÕES =================
def tela_posicoes():
    limpar(main)

    ctk.CTkLabel(main, text="Posições", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)
    ctk.CTkButton(main, text="Criar Posições", command=tela_criar_lote).pack(pady=5)

    canvas = ctk.CTkCanvas(main)
    scroll = ctk.CTkScrollbar(main, command=canvas.yview)
    frame = ctk.CTkFrame(canvas)

    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    col = row = 0
    for pos in posicoes.all():
        codigo = pos["codigo"]
        card = ctk.CTkFrame(frame, width=240, height=150, corner_radius=20)
        card.grid(row=row, column=col, padx=20, pady=20)
        card.grid_propagate(False)

        ctk.CTkLabel(card, text=codigo, font=ctk.CTkFont(size=16, weight="bold")).pack(expand=True)

        card.bind("<Button-1>", lambda e, c=codigo: abrir_posicao(c))

        col += 1
        if col == 4:
            col = 0
            row += 1

def abrir_posicao(codigo):
    limpar(main)

    ctk.CTkLabel(main, text=f"Posição {codigo}", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

    box = ctk.CTkTextbox(main)
    box.pack(expand=True, fill="both", padx=80, pady=20)

    itens = produtos.search((Q.posicao == codigo) & (Q.quantidade > 0))
    if not itens:
        box.insert("end", "Posição vazia\n")
    else:
        for p in itens:
            box.insert("end", f"{p['sku']} | {p['nome']} | Qtd {p['quantidade']}\n")

    ctk.CTkButton(main, text="Voltar", command=tela_posicoes).pack(pady=10)

# ================= CRIAR POSIÇÕES =================
def tela_criar_lote():
    limpar(main)

    ctk.CTkLabel(main, text="Criar Posições", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

    d = ctk.CTkEntry(main, placeholder_text="Depósito")
    li = ctk.CTkEntry(main, placeholder_text="Letra Inicial")
    lf = ctk.CTkEntry(main, placeholder_text="Letra Final")
    p = ctk.CTkEntry(main, placeholder_text="Prateleiras")
    n = ctk.CTkEntry(main, placeholder_text="Níveis")

    for e in (d, li, lf, p, n):
        e.pack(fill="x", padx=80, pady=6)

    def gerar():
        criar_posicoes_em_lote(
            int(d.get()),
            li.get().upper(),
            lf.get().upper(),
            int(p.get()),
            int(n.get())
        )
        tela_posicoes()

    ctk.CTkButton(main, text="Gerar", command=gerar).pack(pady=10)

# ================= MENU =================
def menu_btn(txt, cmd):
    ctk.CTkButton(
        sidebar,
        text=txt,
        height=50,
        command=cmd
    ).pack(fill="x", padx=20, pady=6)

menu_btn("Dashboard", tela_dashboard)
menu_btn("Produtos", tela_produtos)
menu_btn("Consulta", tela_consulta)
menu_btn("Posições", tela_posicoes)

# ================= START =================
tela_dashboard()
app.mainloop()
