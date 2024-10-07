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


from pandas_datareader import data as web
import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime, timedelta
import streamlit as st
import os
import csv
from A1 import executar_operacao




# Carregando os resultados
df_resultados = pd.read_excel('resultados_trading.xlsx')






# Função para calcular o preço de entrada com base no tipo de operação
def calcular_preco_entrada(preco_atual, percentual, tipo_entrada):
    if tipo_entrada == 'Compra na baixa' or tipo_entrada == 'Venda na baixa':
        preco_entrada = preco_atual - (preco_atual * percentual)
    elif tipo_entrada == 'Venda na alta' or tipo_entrada == 'Compra na alta':
        preco_entrada = preco_atual + (preco_atual * percentual)
    
    return preco_entrada


# Função para acionar o código 2 (rastreio)
def rastrear():
    listadas = pd.read_csv('listadas.csv')
    melhores = pd.read_excel('resultados_trading.xlsx')

    listadas['codigos'] = listadas['Ticker'] + '.SA' 
    codigos = listadas['codigos'].tolist()

    data_atual = datetime.now().strftime('%Y-%m-%d')
    # Código 2 que faz o rastreamento dos ativos e cálculos
    # Definindo o intervalo de valores para a variável valor
    valores = [round(x, 3) for x in np.arange(0.01, 0.051, 0.001)]
    # Definindo os valores possíveis para a variável contador
    contadores = [0, 1, 2, -2]
    bet_size = 20

    # Listas para armazenar os resultados
    resultados = []

    # Itera sobre todos os ativos definidos em codigos
    for ativo in codigos:
        x = yf.Ticker(ativo)
        cotacoes = x.history(start='2022-01-01', end=data_atual)

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

        for valor in valores:
            for contador in contadores:
                listadetrades = []
                coma = df.tail(500).iterrows()

                for idx, row in coma:
                    entrada_comprada = row['Fechamento anterior'] - (row['Fechamento anterior']*valor)
                    entrada_vendida = row['Fechamento anterior'] + (row['Fechamento anterior']*valor)
                    entrada_comprada1 = row['Fechamento anterior'] + (row['Fechamento anterior']*valor)
                    entrada_vendida1 = row['Fechamento anterior'] - (row['Fechamento anterior']*valor)

                    if contador == 0:
                        if ((entrada_comprada - row['Mínima']) >= 0):
                            resultado = (row['Fechamento'] - entrada_comprada) * bet_size
                            listadetrades.append({
                                'price': row['Fechamento'],
                                'time': idx,
                                'kind': 'buy',
                                'quantidade': bet_size,
                                'Resultado': resultado,
                                'Entrada': entrada_comprada,
                                'Ajuste': row['A1']
                            })
                    elif contador == 1:
                        if ((entrada_vendida - row['Máxima'])<=0):
                            resultado = (entrada_vendida - row['Fechamento']) * bet_size
                            listadetrades.append({
                                'price': row['Fechamento'],
                                'time': idx,
                                'kind': 'sell',
                                'quantidade': bet_size,
                                'Resultado': resultado,
                                'Entrada': entrada_vendida,
                                'Ajuste': row['A1']
                            })
                    elif contador == 2:
                        if ((entrada_vendida1 - row['Mínima']) >= 0):
                            resultado = (entrada_vendida1 - row['Fechamento']) * bet_size
                            listadetrades.append({
                                'price': row['Fechamento'],
                                'time': idx,
                                'kind': 'sell',
                                'quantidade': bet_size,
                                'Resultado': resultado,
                                'Entrada': entrada_vendida1,
                                'Ajuste': row['A1']
                            })
                    elif contador == -2:
                        if ((entrada_comprada1 - row['Máxima']) <= 0):
                            resultado = (row['Fechamento'] - entrada_comprada1) * bet_size
                            listadetrades.append({
                                'price': row['Fechamento'],
                                'time': idx,
                                'kind': 'buy',
                                'quantidade': bet_size,
                                'Resultado': resultado,
                                'Entrada': entrada_comprada1,
                                'Ajuste': row['A1']
                            })

                # Cria o DataFrame com os trades e calcula o Sharpe Ratio
                df_trades_raw = pd.DataFrame(listadetrades)
                if not df_trades_raw.empty:
                    df_trades1 = df_trades_raw

                    x = ((df_trades1['Resultado'] > 0) == True).sum()
                    y = ((df_trades1['Resultado'] > 0) == False).sum()
                    gain = round((x / (x + y)) * 100, 2)
                    loss = round((y / (x + y)) * 100, 2)

                    df_trades1['ret_acumulado'] = df_trades1['Resultado'].cumsum()
                    tamanho = df_trades1.shape[0]
                    capital_inicial = 100
                    df_trades1['ret_acumulado'] += capital_inicial
                    df_trades1['max_cum'] = df_trades1['ret_acumulado'].cummax()
                    df_trades1['min_cum'] = df_trades1['ret_acumulado'].cummin()
                    draw = df_trades1['drawdown'] = df_trades1['ret_acumulado'] / df_trades1['max_cum'] - 1
                    drawdown = draw.min()

                    sharpe = df_trades1['Resultado'].groupby(df_trades1.index).sum().mean() / (
                                df_trades1['Resultado'].groupby(df_trades1.index).sum().std())

                    resultados.append({
                        'Nome do ativo': ativo,
                        'Quantidade de operações':tamanho,
                        'Valor': valor,
                        'Contador': contador,
                        'Índice Sharpe': sharpe,
                        'Ganho (%)': gain,
                        'Perda (%)': loss,
                        'Drawdown': drawdown
                    })

    # Salva os novos resultados
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_excel('resultados_trading.xlsx', index=False)
    st.success("Rastreamento concluído. Resultados atualizados!")



# Barra de navegação do menu
menu = ["Home", "Relatório", "Monte a sua Operação", "Rastreador", "Análise"]
opcao = st.sidebar.selectbox("Menu", menu)

# Lógica do menu
if opcao == "Home":
    st.title("Bem-vindo ao HC Trading")
    st.write(df_resultados)

elif opcao == "Relatório":
    st.title("Relatório de Resultados")
    exibir_relatorio(df_resultados)

elif opcao == "Monte a sua Operação":
    st.title("Monte a sua Operação")
    
    # Lista suspensa com os ativos disponíveis
    ativo = st.selectbox("Selecione o Ativo", df_resultados['Nome do ativo'].unique())
    
    # Ticker do ativo no formato esperado pelo yfinance
    ticker = ativo  # Supondo que o nome do ativo já seja o ticker. Ajuste se necessário.

    # Obter dados do ativo utilizando yfinance
    dados_ativo = yf.Ticker(ticker)
    historico = dados_ativo.history(period="1d")  # Obter dados do último dia
    
    # Obter o preço de fechamento do último dia
    if not historico.empty:
        preco_abertura = historico['Open'][-1]
    else:
        preco_abertura = 0.0  # Caso não tenha dados disponíveis

    # Campo para preencher o preço atual com o preço de fechamento do último dia
    preco_atual = st.number_input("Preço Atual", value=float(preco_abertura), min_value=0.0, format="%.2f")
    
    # Lista suspensa para selecionar o percentual
    valores = [round(x, 3) for x in np.arange(0, 0.051, 0.001)]
    percentual = st.selectbox("Selecione o Percentual", valores)
    
    # Lista suspensa para selecionar o tipo de entrada
    tipo_entrada = st.selectbox("Selecione o Tipo de Entrada", 
                                ["Compra na baixa", "Venda na alta", "Compra na alta", "Venda na baixa"])
    
    # Botão para calcular o preço de entrada
    if st.button("Calcular Preço"):
        if preco_atual > 0:
            preco_entrada = calcular_preco_entrada(preco_atual, percentual, tipo_entrada)
            st.write(f"### Preço de Entrada Calculado: R$ {preco_entrada:.2f}")
        else:
            st.write("Por favor, insira um preço atual válido.")



elif opcao == "Rastreador":
    st.title("Última Análise")
    st.dataframe(df_resultados)

    # Botão para realizar um novo rastreio
    if st.button("Novo Rastreio"):
        rastrear()
        st.experimental_rerun()

elif opcao == "Análise":
    # Interface do Streamlit
    st.title("Monte a sua Análise")

    # Carregar a lista de ativos
    codigos = pd.read_csv('listadas.csv')
    codigos['Simbol'] = codigos['Ticker'] + '.SA'
    

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

   
    if st.button("Executar Análise"):
        resultado = executar_operacao(valor, tipo_operacao, periodo, ativo_selecionado)
        capital_inicial = 100
        # Exibir os resultados
        st.write("Resultado da Análise:")
        st.dataframe(resultado)

        # Calcular e exibir o pior dia
        pior_dia = round(resultado['Resultado'].min(), 2)

        # Calcular e exibir o melhor dia
        melhor_dia = round(resultado['Resultado'].max(), 2)

        # Calcular e exibir o ganho médio
        ganho_medio = pd.DataFrame()
        ganho_medio['Ganho Médio'] = (resultado['Resultado'] / (resultado['price'] * 10))
        valor = round(ganho_medio['Ganho Médio'].mean() * 100, 2)
        st.markdown(f"""
                ### Dados gerais
            
                - **Ganho médio:** {valor}%
                - **Melhor dia: R$** {melhor_dia}
                - **Pior dia: R$** {pior_dia}
                
                ---
            """)

        # Percentual de Gain e Loss
        x = ((resultado['Resultado'] > 0) == True).sum()
        y = ((resultado['Resultado'] > 0) == False).sum()
        gain = round((x / (x + y)) * 100, 2)
        loss = round((y / (x + y)) * 100, 2)
        lucro = (resultado['Resultado'].sum())
        st.markdown(f"""
                ### Avaliação geral do ativo: **{ativo_selecionado}**
                
                - **Percentual de acerto:** {gain}%
                - **Percentual de erro:** {loss}%
                - **Lucro: R$** {round(resultado['Resultado'].sum(),2)}
                - **Capital final: R$** {round(capital_inicial+lucro,2)}
                
                ---
            """)

        # Avaliação da estratégia
        resultado['ret_acumulado'] = resultado['Resultado'].cumsum()
        st.write("Gráfico de Retorno Acumulado:")
        st.line_chart(resultado['ret_acumulado'])

        # DrawDown
        resultado['ret_acumulado'] += capital_inicial
        lucro = round(resultado['Resultado'].sum(), 2)
        drawdown = resultado['ret_acumulado'] - resultado['ret_acumulado'].cummax()
        resultado['drawdown'] = drawdown

        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(20, 8))
        ax[0].plot(resultado['ret_acumulado'])
        ax[0].set_title("Retorno Acumulado")
        ax[1].plot(resultado['drawdown'], color='red')
        ax[1].set_title("Drawdown")
        st.pyplot(fig)

        # Calculando o período de drawdown
        resultado['underwater'] = resultado['ret_acumulado'] < resultado['ret_acumulado'].cummax()
        periodo_drawdown = round(resultado['underwater'].sum() / 8, 2)
        st.write(f"Período de drawdown: {periodo_drawdown}")