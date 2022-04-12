import dash
from dash import html
from dash import dcc
from dash import dash_table

from dash.dependencies import Input, Output

from webscraping_v3 import *

import sys

from dash.exceptions import PreventUpdate

import requests

external_stylesheets = ['http://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(external_stylesheets=external_stylesheets)

## 優化:  ------------------------------------------------------------------
def reusable_graph_table(name): ##此name用來 :1.定義圖表和DataTable的id。 2.設定Output和建立function名稱
    ##步聚一: 建立Div標籤，存到div變數
    div = html.Div(           ## 可依序放左或右邊欄
        className='one-half column', ## 規定此html的Div標籤，只會佔所在row的一半。
        children=[       
            dcc.Graph(id=f'{name}-fig'),
            dash_table.DataTable(        
                id=f'{name}-df',
                style_table={'height': '250px','overflowY': 'auto'},
                page_size=20,     
                fixed_rows={'headers': True}
            )
        ]
    )
    ## 步驟二 : 設定Output
    @app.callback([           # 相較之前作法，此時的callback funtion獨立了，即依幾張圖表就發出幾個請求，達到分流效果而增加查詢速度
        Output(f'{name}-fig', 'figure'),
        Output(f'{name}-df', 'columns'),
        Output(f'{name}-df', 'data')],
        Input('stock-list-dropdown', 'value'))

    ## 步驟三 : 呼叫爬蟲程式
    def update_output(symbol): 
        
        if not symbol:         # 我:口語化 : 若symbol為不正常( 即 非True )，則產生exception停止更新。
            raise PreventUpdate
        symbol = symbol.split('.')[0]
        
        func = getattr(sys.modules[__name__], f'get_{name}') ##我:getattr(主程式,屬性的名稱)，在主程式當中，取得該 屬性名稱 的 值(我:就是一個程式或曰物件)，並存到變數func中。 
        
        df, fig = func(symbol)
        columns = [get_column_dict(column, dtype) for column, dtype in df.dtypes.items()]
        data = df.to_dict(orient='records')

        return fig, columns, data
    
    ## 步驟四 : 回傳div變數
    return div

# 優化結束------------------------------------------------------------------------------------------------------------

app.layout = html.Div(         # 最外層的包裝
    className='container',     # 我:app已套用外部樣式，此「className」「container」等…皆外部樣式的特定用字。或許這麼說才對:這些用字是dash的html套件定義的，而外部樣式支援之。
    style={
        'marginTop': 60,
        'marginBottom': 60,
        'textAlign': 'center'
    },
    children=[                
        html.Div(        # 建立第一個 row(會放標題及下拉式選單)，一樣，給它一個 Div標籤
            className='row',
            style={
                'marginBottom':30, 
            },
            children=[          # 第一個 row(會放標題及下拉式選單)
                html.H3('專屬 VIP 看盤室'),
                dcc.Dropdown(
                    id='stock-list-dropdown',
                    options=get_stock_list(),
                    placeholder='搜尋台股代號/名稱' 
                )
            ]
        ),
        html.Div(      # 第二個row
            className='row',
            children=[            # 中放二欄，寬度是二分之一，一樣，各給一個 Div標 籤  
                reusable_graph_table('shareholder_structure'),  
                reusable_graph_table('inst_investors')
            ]
        ),
        html.Hr(),                ## 水平分割線
        html.Div(      # 第三個row中
            className='row',
            children=[            # 放二欄，寬度是二分之一，一樣，各給一個 Div標籤
                reusable_graph_table('monthly_revenue'),
                reusable_graph_table('cashflow')
            ]
        ),
        html.Hr(),
        html.Div(      # 第四個row中
            className='row',
            children=[            # 放二欄，寬度是二分之一，一樣，各給一個Div標籤
                reusable_graph_table('profitability'),
                reusable_graph_table('dividends')
            ]
        )        
    ]
)

if __name__ == '__main__':
    app.run_server()