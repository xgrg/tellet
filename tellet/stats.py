from tellet import get_users



def get_doughnut(df, label='My dataset', ws='cha'):
    labels = get_users()[ws]
    data = []
    for i in labels:
        data.append(len(df.query('who == "%s" & action == "did"' % i)))

    graph = {'labels': labels,
             'datasets': [{'label': label,
                           'data': data,
                           'backgroundColor': ['rgb(54, 162, 235)',
                                               'rgb(255, 99, 132)'],
                           'hoverOffset': 4}]}

    config = {'type': 'doughnut',
              'data': graph}
    return config


def get_radar(df, label='My dataset', ws='cha'):
    labels = get_users()[ws]

    actions = ['aspirateur', 'lavevaisselle', 'linge', 'lessive',
               'litière', 'nettoyer', 'pavé', 'douche', 'wc', 'piscine',
               'poubelles', 'cuisine', 'autres']
    sorted_actions = {}
    for i, row in df.iterrows():
        if row.action != 'did' or str(row['where']) != 'reports': continue
        sorted_actions.setdefault(row.who, {})
        what = row.what
        has_found = False
        for a in actions[:-1]:
            sorted_actions[row.who].setdefault(a, [])
            if what.startswith(a):
                sorted_actions[row.who][a].append(what)
                has_found = True
        if not has_found:
            sorted_actions[row.who].setdefault('autres', [])
            sorted_actions[row.who]['autres'].append(row.what)
    # print(sorted_actions['Cha']['autres'])
    # print(sorted_actions['Greg']['autres'])

    datasets = []
    colors = [{'backgroundColor': 'rgba(54, 162, 235, 0.2)',
               'borderColor': 'rgb(54, 162, 235)',
               'pointBackgroundColor': 'rgb(54, 162, 235)',
               'pointBorderColor': '#fff',
               'pointHoverBackgroundColor': '#fff',
               'pointHoverBorderColor': 'rgb(54, 162, 235)'},
              {'backgroundColor': 'rgba(255, 99, 132, 0.2)',
               'borderColor': 'rgb(255, 99, 132)',
               'pointBackgroundColor': 'rgb(255, 99, 132)',
               'pointBorderColor': '#fff',
               'pointHoverBackgroundColor': '#fff',
               'pointHoverBorderColor': 'rgb(255, 99, 132)'}]

    for who, c in zip(labels, colors):
        d = {'label': who,
             'data': [len(sorted_actions.get(who, {}).get(a, [])) for a in actions],
             'fill': True}
        d.update(c)
        datasets.append(d)

    data = {'labels': actions,
            'datasets': datasets}
    options = {'elements': {'line': {'borderWidth': 3}},
               'plugins': {'colorschemes': {'scheme': 'brewer.SetThree12'}}}

    config = {'type': 'radar',
              'data': data,
              'options': options}
    return config


def get_stacked_doughnut(df, ws='cha'):
    labels = get_users()[ws]
    sorted_actions = {}
    for i, row in df.iterrows():
        if row.action != 'did' or str(row['where']) != 'reports': continue
        sorted_actions.setdefault(row.who, {})
        items = row.what.split(';')
        what = items[0]
        duration = items[2]
        sorted_actions[row.who].setdefault(duration, [])
        sorted_actions[row.who][duration].append(what)

    d1 = [len(sorted_actions.get(labels[0], {}).get(e, [])) for e in '012345']
    d2 = [len(sorted_actions.get(labels[1], {}).get(e, [])) for e in '012345']

    data = {'labels': ['<1 min', '1-7 min', '10-15 min', '20-30 min',
                       '>30 min', '>2 h'],
            'datasets': [{'label': labels[1],
                          'data': d1,
                          'borderColor': 'rgb(255, 99, 132)',
                          'backgroundColor': 'rgba(255, 99, 132, 0.2)'},
                         {'label': labels[0],
                          'data': d2,
                          'borderColor': 'rgb(54, 162, 235)',
                          'backgroundColor': 'rgba(54, 162, 235, 0.2)'}]}

    config = {'type': 'bar',
              'data': data,
              'options': {
                'indexAxis': 'y',
                'elements': {'bar': {'borderWidth': 2}},
                'responsive': True,
                'plugins': {
                  'legend': {'position': 'right'}
                 }
              }}
    return config
