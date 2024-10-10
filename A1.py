# ========================================================
# hTradingBacktest - Ferramenta de Backtest para o Mercado de Ações
# 
# Copyright © Henrique Couto Toledo. Todos os direitos reservados.
# 
# Este código é uma ferramenta de backtest para análise de estratégias
# no mercado de ações, e está sujeito a proteção de direitos autorais.
# Nenhuma parte deste código pode ser reproduzida ou distribuída sem
# permissão expressa do autor.
#
# Criado por: Henrique Couto Toledo
# ========================================================
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt

# Função que executa a lógica de cálculo
# Função que executa a lógica de cálculo
def executar_operacao(valor, tipo_operacao, periodo, ativo_selecionado, sentido):
    # Define o contador com base no tipo de operação
    contador = 0
    if tipo_operacao == "Compra na baixa":
        contador = 0
    elif tipo_operacao == "Venda na alta":
        contador = 1
    elif tipo_operacao == "Venda na baixa":
        contador = 2
    elif tipo_operacao == "Compra na alta":
        contador = -2

    bet_size = 100
    listadetrades = []

    # Baixa os dados do ativo selecionado
    ativo = yf.Ticker(ativo_selecionado)
    data_atual = datetime.now().strftime('%Y-%m-%d')
    cotacoes = ativo.history(start='2014-01-01', end=data_atual) 

    # Cria o DataFrame com os dados de cotações
    df = pd.DataFrame()
    df.index = cotacoes.index
    df['Abertura'] = cotacoes['Open']
    df['Fechamento anterior']=cotacoes['Close'].shift(1)
    df['Fechamento'] = cotacoes['Close']
    df['Máxima'] = cotacoes['High']
    df['Mínima'] = cotacoes['Low']
    df['Volume'] = cotacoes['Volume']
    df['Atual'] = cotacoes['Close'] - cotacoes['Open']
    df['A1'] = cotacoes['Close'].shift(1) - cotacoes['Open'].shift(1)
    df['A2'] = cotacoes['Close'].shift(2) - cotacoes['Open'].shift(2)

    if sentido == "Dados antigos":
        df = df.head(periodo).iterrows()
    elif sentido == "Dados atuais":
        df = df.tail(periodo).iterrows()

    for idx, row in df:
        entrada_comprada = row['Fechamento anterior'] - (row['Fechamento anterior']*valor)
        entrada_vendida = row['Fechamento anterior'] + (row['Fechamento anterior']*valor)
        entrada_comprada1 = row['Fechamento anterior'] + (row['Fechamento anterior']*valor)
        entrada_vendida1 = row['Fechamento anterior'] - (row['Fechamento anterior']*valor)
        
        # Lógica de operações baseada no tipo
        if contador == 0 and ((entrada_comprada - row['Mínima']) >= 0):
            resultado = (row['Fechamento'] - entrada_comprada) * bet_size
            listadetrades.append({
                'price': row['Fechamento'], 'time': idx, 'kind': 'buy',
                'quantidade': bet_size, 'Resultado': resultado, 'Entrada': entrada_comprada
            })
        elif contador == 1 and ((entrada_vendida - row['Máxima'])<=0):
            resultado = (entrada_vendida - row['Fechamento']) * bet_size
            listadetrades.append({
                'price': row['Fechamento'], 'time': idx, 'kind': 'sell',
                'quantidade': bet_size, 'Resultado': resultado, 'Entrada': entrada_vendida
            })
        elif contador == 2 and ((entrada_vendida1 - row['Mínima'])) >= 0:
            resultado = (entrada_vendida1 - row['Fechamento']) * bet_size
            listadetrades.append({
                'price': row['Fechamento'], 'time': idx, 'kind': 'sell',
                'quantidade': bet_size, 'Resultado': resultado, 'Entrada': entrada_vendida1
            })
        elif contador == -2 and ((entrada_comprada1 - row['Máxima']) <= 0):
            resultado = (row['Fechamento'] - entrada_comprada1) * bet_size
            listadetrades.append({
                'price': row['Fechamento'], 'time': idx, 'kind': 'buy',
                'quantidade': bet_size, 'Resultado': resultado, 'Entrada': entrada_comprada1
            })

    # Converte a lista de trades para DataFrame
    df_trades_raw = pd.DataFrame(listadetrades)
    return df_trades_raw

# Interface do Streamlit
st.title("Monte a sua Operação")

# Carregar a lista de ativos
codigos = pd.read_excel('selecao.xlsx')
codigos['Simbol'] = codigos['codigo'] + '.SA'

# Campo para o usuário selecionar o ativo
ativo_selecionado = st.selectbox(
    "Selecione o Ativo",
    codigos['Simbol']
)

# Campo para o usuário digitar o valor percentual
valor = st.number_input("Digite o valor percentual (ex: 0.02 para 2%)", min_value=0.0, format="%.4f")

# Campo para o usuário selecionar o tipo de operação
tipo_operacao = st.selectbox(
    "Selecione o Tipo de Operação",
    ["Compra na baixa", "Venda na alta", "Venda na baixa", "Compra na alta"]
)

# Campo para o usuário inserir o período (número de dias)
periodo = st.number_input("Período (número de dias)", min_value=1, step=1)

# Botão para executar a operação
if st.button("Executar Operação"):
    resultado = executar_operacao(valor, tipo_operacao, periodo, ativo_selecionado)
    
    # Exibir os resultados
    st.write("Resultado da Operação:")
    st.dataframe(resultado)

    