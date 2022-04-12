# import sqlalchemy stackoverflow的該提問者所需求的解法，故vs code建議刪除沒用到的package
# import mongoengine


import pandas as pd
import random
import requests

import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Group

percentage_format = FormatTemplate.percentage(2)
group_format = Format().group(True)

base_urls = [
    'https://justdata.moneydj.com/', # MoneyDJ
    'http://jdata.yuanta.com.tw/',  # 元大
    'https://fubon-ebrokerdj.fbs.com.tw/', # 富邦
    'http://moneydj.emega.com.tw/', # 兆豐
    'http://newjust.masterlink.com.tw/' # 元富
]

def get_stock_list():
    
    tse_url = 'https://isin.twse.com.tw/isin/class_main.jsp?market=1&issuetype=1&Page=1&chklike=Y'
    otc_url = 'https://isin.twse.com.tw/isin/class_main.jsp?market=2&issuetype=4&Page=1&chklike=Y'
    
    tse_df = pd.read_html(requests.get(tse_url).text, header=0)[0]
    otc_df = pd.read_html(requests.get(otc_url).text, header=0)[0]
    
    options = []

    for index, row in tse_df.iterrows():
        options.append({
            'label': f"{row['有價證券代號']} {row['有價證券名稱']} - {row['市場別']} ({row['產業別']})",
            'value': f"{row['有價證券代號']}.TW"
        })
    for index, row in otc_df.iterrows():
        options.append({
            'label': f"{row['有價證券代號']} {row['有價證券名稱']} - {row['市場別']} ({row['產業別']})",
            'value': f"{row['有價證券代號']}.TWO"
        })
        
    return options


def get_column_dict(column, dtype):
    
    if '率' in column:
        return {"name": column, "id": column, "type": 'numeric', "format": percentage_format}
    
    elif pd.api.types.is_numeric_dtype(dtype):
        return {"name": column, "id": column, "type": 'numeric', "format": group_format}
    
    else:
        return {"name": column, "id": column}
    
def get_shareholder_structure(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcj/zcj_{symbol}.djhtm'
    dfs = pd.read_html(url)
    df = dfs[3]
    
    df = df.iloc[2:-1, [0, 1, 3]]
    df.columns = ['項目', '持股張數', '持股比率']
    
    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df['持股比率'] = df['持股比率'] / 100
    others_percentage = round(1 - df['持股比率'].sum(), 4)
    others = int(df['持股張數'].sum() / df['持股比率'].sum() * others_percentage)
    
    new_row = {
        '項目': '其他',
        '持股張數': others,
        '持股比率': others_percentage
    }

    df = df.append(new_row, ignore_index=True)
    
    fig = px.pie(df, names='項目', values='持股張數', title=f'{symbol} 籌碼分布圖')
    fig.update_traces(textinfo='label+percent')
    
    return df, fig


def get_dividends(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcc/zcc_{symbol}.djhtm'
    
    html = requests.get(url).text   
    html = html.replace('<td class="t3n0">', '<tr><td class="t3n0">')
    
    dfs = pd.read_html(html)
    df = dfs[2]
    
    df = df.iloc[4:, [0, 3, 4, 5, 7]]
    df.columns = ['年度', '現金股利' , '盈餘配股', '公積配股', '合計']
    df = df[~df['年度'].str.contains('Q')]
    
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.round(4)
    
    fig_df = df.iloc[:12]
    fig = px.bar(fig_df, x='年度', y='合計', text='合計')
    fig.update_layout(
        title=f'{symbol} 歷年股利',
        yaxis_title='元',
        xaxis_title='年度',
        template='plotly_white',
    )

    return df, fig


def get_inst_investors(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zcl/zcl.djhtm?a={symbol}&b=3'
    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[7:, :5]
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df.columns = ['日期', '外資', '投信', '自營商', '合計']

    fig_df = df.iloc[:-1][::-1]
    
    fig = px.bar(fig_df, x='日期', y=['外資','投信', '自營商'])
    
    fig.update_layout(
        title=f'{symbol} 三大法人',
        xaxis_title='日期',
        yaxis_title='張',
        template='plotly_white',
        hovermode='x unified',
    )
    
    return df, fig


def get_cashflow(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zc3/zc3_{symbol}.djhtm'
    
    r = requests.get(url)
    html = r.text.replace('div class="table-caption', 'tr class="table-caption')
    html = html.replace('div class="table-row', 'tr class="table-row')
    html = html.replace('span class="table-cell', 'td class="table-cell')

    dfs = pd.read_html(html)
    df = dfs[1]
    
    df.set_index(0, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    
    data = {
        '季別': df.loc['期別'],
        '淨現金流': df.loc['本期產生現金流量'].apply(pd.to_numeric),
        '營業活動': df.loc['來自營運之現金流量'].apply(pd.to_numeric),
        '投資活動': df.loc['投資活動之現金流量'].apply(pd.to_numeric),
        '融資活動': df.loc['籌資活動之現金流量'].apply(pd.to_numeric)
    }
    
    df = pd.DataFrame(data)
    
    fig_df = df.iloc[::-1]
    
    fig = px.scatter(fig_df, x=fig_df['季別'], y=['淨現金流','營業活動', '投資活動', '融資活動'])
    fig.update_traces(mode='markers+lines')
    fig.update_layout(
        title=f'{symbol} 現金流量表',
        xaxis_title='季別',
        yaxis_title='百萬',
        template='plotly_white',
        hovermode='x unified'
    )
    return df, fig


def get_monthly_revenue(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zch/zch_{symbol}.djhtm'
    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[6:, :3]
    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    
    df = df.apply(pd.to_numeric, errors='ignore')
    df[2] = df[2] / 100
    
    df.columns = ['日期', '營業收入', '月增率']
    
    fig_df = df.iloc[:12][::-1]
    
    fig = make_subplots(specs=[[{'secondary_y': True}]])

    fig.add_trace(
        go.Bar(x=fig_df['日期'], y=fig_df['營業收入'], name='營業收入'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=fig_df['日期'], y=fig_df['月增率'], name='月增率'),
        secondary_y=True,
    )

    fig.update_layout(
        title_text=f'{symbol} 月營收表',
        xaxis_title='日期',
        template='plotly_white',
        hovermode='x unified',
        yaxis1_title='營業收入',
        yaxis2_title='月增率',
        yaxis2_tickformat='p',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return df, fig


def get_profitability(symbol):
    
    url = f'{random.choice(base_urls)}z/zc/zce/zce_{symbol}.djhtm'

    dfs = pd.read_html(url)
    df = dfs[2]
    
    df = df.iloc[3:, [0, 1, 4, 6, 8, 9, 10]]
    df.replace('%', '', regex=True, inplace=True)
    df.replace('--', '', regex=True, inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    
    df[8] = (df[8] / df[1]).round(4)
    df[9] = (df[9] / df[1]).round(4)
    del df[1]
    
    df[4] = df[4] / 100
    df[6] = df[6] / 100
    
    df.columns = ['季別', '毛利率' , '營益率', '稅前淨利率' ,'稅後淨利率', 'EPS(元)']
    
    fig_df = df.iloc[:12][::-1]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=fig_df['季別'], y=fig_df['EPS(元)'], name='EPS(元)'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=fig_df['季別'], y=fig_df['毛利率'], name='毛利率'),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(x=fig_df['季別'], y=fig_df['營益率'], name='營益率'),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(x=fig_df['季別'], y=fig_df['稅前淨利率'], name='稅前淨利率'),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(x=fig_df['季別'], y=fig_df['稅後淨利率'], name='稅後淨利率'),
        secondary_y=True
    )

    fig.update_layout(
        title_text=f'{symbol} 獲利能力',
        xaxis_title='季別',
        template='plotly_white',
        hovermode='x unified',
        yaxis1_title='EPS(元)',
        yaxis2_tickformat='p',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return df, fig