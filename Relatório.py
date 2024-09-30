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

# Função para exibir o relatório dos melhores resultados
def exibir_relatorio(df):
    melhores_resultados = df[
        (df['Índice Sharpe'] > 0.4) & (df['Índice Sharpe'] < 1) & (df['Ganho (%)'] > 75)
    ]
    
    if not melhores_resultados.empty:
        st.write("## Melhores Resultados")
        
        for _, row in melhores_resultados.iterrows():
            percentual_acerto = row['Ganho (%)']
            percentual_erro = 100 - percentual_acerto
            tipo_operacao = ""
            if row['Contador'] == 0:
                tipo_operacao = "Compra na baixa"
            elif row['Contador'] == 1:
                tipo_operacao = "Venda na alta"
            elif row['Contador'] == 2:
                tipo_operacao = "Venda na baixa"
            elif row['Contador'] == -2:
                tipo_operacao = "Compra na alta"
            
            nivel_percentual = row['Valor'] * 100
            
            # Exibindo cada resultado com formatação mais profissional
            st.markdown(f"""
                ### Ativo: **{row['Nome do ativo']}**
                
                - **Índice Sharpe:** {row['Índice Sharpe']:.2f}
                - **Ganho (%):** {percentual_acerto:.2f}%
                - **Perda (%):** {percentual_erro:.2f}%
                - **Tipo de operação:** {tipo_operacao}
                - **Nível percentual de compra ou venda:** {nivel_percentual:.2f}%
                
                ---
            """)
    else:
        st.write("Nenhum resultado atende aos critérios de seleção.")

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
    valores = [0.01, 0.02, 0.03, 0.04, 0.05]
    # Definindo os valores possíveis para a variável contador
    contadores = [0, 1, 2, -2]
    bet_size = 100

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
        df['Fechamento'] = cotacoes['Close']
        df['Máxima'] = cotacoes['High']
        df['Mínima'] = cotacoes['Low']
        df['Volume'] = cotacoes['Volume']
        df['Atual'] = cotacoes['Close'] - cotacoes['Open']
        df['A1'] = cotacoes['Close'].shift(1) - cotacoes['Open'].shift(1)
        df['A2'] = cotacoes['Close'].shift(2) - cotacoes['Open'].shift(2)

        # Calcula as variações
        Var_Fechamento = df['Fechamento'] / df['Fechamento'].shift(1) - 1
        Var_Abertura = df['Abertura'] / df['Fechamento'].shift(1) - 1
        Var_Maxima = df['Máxima'] / df['Fechamento'].shift(1) - 1
        Var_Minima = df['Mínima'] / df['Fechamento'].shift(1) - 1

        df1 = pd.DataFrame()
        df1['Abertura'] = Var_Abertura
        df1['Fechamento'] = Var_Fechamento
        df1['Maxima'] = Var_Maxima
        df1['Mínima'] = Var_Minima

        for valor in valores:
            for contador in contadores:
                listadetrades = []
                coma = df.tail(250).iterrows()

                for idx, row in coma:
                    entrada_comprada = row['Abertura'] - (row['Abertura'] * valor)
                    entrada_vendida = row['Abertura'] + (row['Abertura'] * valor)
                    entrada_comprada1 = row['Abertura'] + (row['Abertura'] * valor)
                    entrada_vendida1 = row['Abertura'] - (row['Abertura'] * valor)

                    if contador == 0:
                        if ((entrada_comprada - row['Mínima']) >= 0) and (row['A1'] < 0):
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
                        if (entrada_vendida <= row['Máxima']) and (row['A1'] > 0):
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
                        if ((entrada_vendida1 - row['Mínima']) >= 0) and (row['A1'] < 0):
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
                        if (entrada_comprada1 - row['Máxima']) <= 0:
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
    historico = dados_ativo.history(period="2d")  # Obter dados do último dia
    
    # Obter o preço de fechamento do último dia
    if not historico.empty:
        preco_fechamento = historico['Close'][-2]
    else:
        preco_fechamento = 0.0  # Caso não tenha dados disponíveis

    # Campo para preencher o preço atual com o preço de fechamento do último dia
    preco_atual = st.number_input("Preço Atual", value=float(preco_fechamento), min_value=0.0, format="%.2f")
    
    # Lista suspensa para selecionar o percentual
    percentual = st.selectbox("Selecione o Percentual", [0.01, 0.02, 0.03, 0.04, 0.05])
    
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
        
        # Exibir os resultados
        st.write("Resultado da Análise:")
        st.dataframe(resultado)

        # Calcular e exibir o pior dia
        pior_dia = round(resultado['Resultado'].min(), 2)
        st.write(f"Pior dia: R$ {pior_dia}")

        # Calcular e exibir o melhor dia
        melhor_dia = round(resultado['Resultado'].max(), 2)
        st.write(f"Melhor dia: R$ {melhor_dia}")

        # Calcular e exibir o ganho médio
        ganho_medio = pd.DataFrame()
        ganho_medio['Ganho Médio'] = (resultado['Resultado'] / (resultado['price'] * 10))
        valor = round(ganho_medio['Ganho Médio'].mean() * 100, 2)
        st.write(f"Ganho médio: {valor}% ao dia")

        # Percentual de Gain e Loss
        x = ((resultado['Resultado'] > 0) == True).sum()
        y = ((resultado['Resultado'] > 0) == False).sum()
        gain = round((x / (x + y)) * 100, 2)
        loss = round((y / (x + y)) * 100, 2)
        st.write(f"Percentual de acerto: {gain}%")
        st.write(f"Percentual de erro: {loss}%")

        # Avaliação da estratégia
        resultado['ret_acumulado'] = resultado['Resultado'].cumsum()
        st.write("Gráfico de Retorno Acumulado:")
        st.line_chart(resultado['ret_acumulado'])

        # DrawDown
        capital_inicial = 1000
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