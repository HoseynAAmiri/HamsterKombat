import dash
from dash import dcc, dash_table, html, Input, Output, State
import numpy as np
import pandas as pd

# Load the initial data
file_path = './my_hamster.csv'
data = pd.read_csv(file_path)


# Preprocess the data
def preprocess_data(data):
    data['Current PPH'] = data['Current PPH'].astype(int)
    data['Upgrade price'] = data['Upgrade price'].astype(int)
    data['Upgrade PPH'] = data['Upgrade PPH'].astype(int)
    return data


# Estimate cumulative cost based on a multiplier
def estimate_cumulative_cost(row, multiplier):
    level = row['Level']
    initial_cost = int(row['Upgrade price']) / \
        (multiplier ** (int(level) - 1))
    cumulative_cost = sum(initial_cost * (multiplier ** i)
                          for i in range(int(level)))
    return int(cumulative_cost)


def calculate_cumulative_cost(data, multiplier=1.5):
    data['Cumulative Cost'] = data.apply(
        lambda row: estimate_cumulative_cost(row, multiplier), axis=1)
    return data


# Calculate NPV
def calculate_npv(data, discount_rate=0.1, time_period=10):
    npvs = []
    for index, row in data.iterrows():
        cash_flows = [(row['Current PPH'] * 24 * 365) / ((1 + discount_rate) ** t)
                      for t in range(1, time_period + 1)]
        npv = sum(cash_flows) - \
            (row['Cumulative Cost'] + row['Upgrade price'])
        npvs.append(npv)
    data['NPV'] = np.round(np.array(npvs) / np.mean(npvs), 2)
    return data


# Calculate Efficiency
def calculate_efficiency(data):
    efficiency = np.log10(data['Upgrade PPH'] / data['Upgrade price'])
    data['Efficiency'] = np.round(np.mean(efficiency) / efficiency, 3)
    return data


# Combined metric of NPV and Efficiency
def combined_metric(data):
    combined = data['NPV'] * 10 ** data['Efficiency']
    data['Combined Metric'] = np.round(np.log10(combined), 3)
    return data


data = preprocess_data(data)
data = calculate_cumulative_cost(data)
data = calculate_npv(data)
data = calculate_efficiency(data)
data = combined_metric(data)

app = dash.Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in data.columns],
        data=data.to_dict('records'),
        editable=True,
        hidden_columns=['Cumulative Cost'],
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        page_action='native',
        page_current=0,
        page_size=20,
    ),
    html.Button('Save Changes', id='save-button', n_clicks=0),
    dcc.Store(id='stored-data', data=data.to_dict('records'))
])


@app.callback(
    Output('stored-data', 'data'),
    Input('save-button', 'n_clicks'),
    State('table', 'data'),
    prevent_initial_call=True
)
def save_data(n_clicks, rows):
    updated_data = pd.DataFrame(rows)
    updated_data.to_csv(file_path, index=False)
    return updated_data.to_dict('records')


@app.callback(
    Output('table', 'data'),
    Input('stored-data', 'data')
)
def update_table(stored_data):
    data = pd.DataFrame(stored_data)
    data = preprocess_data(data)
    data = calculate_cumulative_cost(data)
    data = calculate_npv(data)
    data = calculate_efficiency(data)
    data = combined_metric(data)
    data = data.sort_values(by='Combined Metric', ascending=False)
    return data.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
