from shapely.geometry import Point, Polygon
import geopandas as gpd
from lxml import etree
import json
from dash import dcc, html, dash_table, Input, Output, State
import dash
import plotly.graph_objects as go
from tkinter import filedialog, Tk
from func import group, owner, user


def select_file():
    tk = Tk()
    tk.withdraw()
    file_path = filedialog.askopenfilename(
        title="Wybierz plik",
        filetypes=[("Plik XML", "*.xml")]
    )
    tk.destroy()
    return file_path


def polygon_from_gml(object_name, namespaces):
    polygons = []
    xpath_expression = f".//{object_name}"
    for element in root.findall(xpath_expression, namespaces=namespaces):
        exterior_element = element.find(".//gml:exterior", namespaces=namespaces)
        if exterior_element is not None:
            position_list = exterior_element.find(".//gml:posList", namespaces=namespaces)
            if position_list is not None and position_list.text:
                coordinates = list(map(float, position_list.text.split()))
                coordinate_pairs = [
                    (coordinates[i + 1], coordinates[i]) for i in range(0, len(coordinates), 2)
                ]
                polygons.append(Polygon(coordinate_pairs))
    return polygons


def transform_to_crs(geometry_list, crs="EPSG:4326"):
    gdf = gpd.GeoDataFrame(geometry=geometry_list, crs="EPSG:2178")
    return gdf.to_crs(crs=crs)


def shape_drawer(fig, dataframe, group_name, attributes, color, width, label):
    def get_label_value(attribute, label):
        if isinstance(label, list):
            return " ".join([attribute.get(l, None) for l in label])
        return attribute.get(label, None)

    def add_polygon_trace(row, group_name, color, width, label_value, attribute):
        x, y = row.geometry.exterior.xy
        serialized_attr = json.dumps(attribute, ensure_ascii=False)
        fig.add_trace(go.Scattermapbox(
            lat=list(y), lon=list(x), mode='lines', line=dict(width=width, color=color),
            name=group_name, customdata=[serialized_attr] * len(x), hovertemplate="",
            text=group_name, hoverinfo='text', legendgroup=group_name, showlegend=False
        ))
        return x, y, serialized_attr

    def add_label_trace(centroid, label_value, serialized_attr, group_name, color):
        fig.add_trace(go.Scattermapbox(
            lat=[centroid.y], lon=[centroid.x], mode='text', name=label_value,
            customdata=[serialized_attr], text=label_value, textfont=dict(size=10, color=color),
            showlegend=False, hoverinfo='text', legendgroup=group_name
        ))
    for i, row in dataframe.iterrows():
        if isinstance(row.geometry, Polygon):
            attribute = attributes[i]
            label_value = get_label_value(attribute, label)
            x, y, serialized_attr = add_polygon_trace(row, group_name, color, width, label_value, attribute)
            centroid = row.geometry.centroid
            add_label_trace(centroid, label_value, serialized_attr, group_name, color)
            if i == 0:
                fig.data[-2].showlegend = True


def fetch_attributes(object_name, ns_dict):
    ignored_tags = ['startObiekt', 'startWersjaObiekt', 'EGB_IdentyfikatorIIP']

    def extract_recursive(node):
        attributes = {}
        for subnode in node:
            node_name = etree.QName(subnode.tag).localname
            if node_name.lower() == 'geometria' or node_name in ignored_tags:
                continue
            if len(subnode):
                nested = extract_recursive(subnode)
                if nested:
                    attributes[node_name] = nested
            else:
                text_value = subnode.text.strip() if subnode.text else None
                if text_value:
                    attributes[node_name] = text_value
        return attributes

    result = []
    for element in root.xpath(f".//{object_name}", namespaces=ns_dict):
        extracted = extract_recursive(element)
        if extracted:
            if object_name in points_namespaces:
                position = element.find(".//gml:pos", namespaces=ns_dict)
                if position is not None:
                    extracted['pos'] = position.text.strip()
            result.append(extracted)

    return result


def expand_keys(attributes):
    output = {}

    def explore(nested_key, item):
        if isinstance(item, dict):
            for sub_key, sub_value in item.items():
                explore(f"{nested_key}__{sub_key}" if nested_key else sub_key, sub_value)
        else:
            output[nested_key] = item

    for main_key, content in attributes.items():
        explore(main_key, content)

    return output


def extract_namespace_ref(namespace, root_element, object_root, original_tag, reference_tag, field_name):
    ref_elements = object_root.findall(f'egb:{reference_tag}', namespaces=namespace)
    original_elements = root_element.findall(f'.//egb:{original_tag}', namespaces=namespace)

    original_dict = {
        orig.get('{http://www.opengis.net/gml/3.2}id'): orig
        for orig in original_elements if orig.get('{http://www.opengis.net/gml/3.2}id')
    }

    result_names = []

    for reference in ref_elements:
        link = reference.get('{http://www.w3.org/1999/xlink}href')
        if not link:
            continue
        element_id = link.lstrip('#')
        corresponding_element = original_dict.get(element_id)
        if corresponding_element is None:
            continue

        if isinstance(field_name, list):
            combined_name = " ".join(
                corresponding_element.findtext(f'egb:{field}', namespaces=namespace) or "" for field in field_name
            )
        else:
            combined_name = corresponding_element.findtext(f'egb:{field_name}', namespaces=namespace) or ""
        result_names.append(combined_name)

    return result_names


def extract_data(namespaces):
    parcels = []

    for parcel in root.findall('.//egb:EGB_DzialkaEwidencyjna', namespaces=namespaces):
        parcel_id = parcel.get('{http://www.opengis.net/gml/3.2}id')
        identifier = parcel.findtext('egb:idDzialki', namespaces=namespaces)
        land_register = parcel.findtext('egb:numerKW', namespaces=namespaces)
        area_element = parcel.find('egb:poleEwidencyjne', namespaces=namespaces)
        area = area_element.text if area_element is not None else None
        unit_of_measurement = area_element.get('uom') if area_element is not None else None
        additional_info = parcel.findtext('egb:dodatkoweInformacje', namespaces=namespaces)
        tech_docs = extract_namespace_ref(namespaces, root, parcel, 'EGB_OperatTechniczny', 'operatTechniczny2', 'identyfikatorOperatuWgPZGIK')
        boundary_points = extract_namespace_ref(namespaces, root, parcel, 'EGB_PunktGraniczny', 'punktGranicyDzialki', 'idPunktu')
        boundary_point_count = len(boundary_points)
        modifications = extract_namespace_ref(namespaces, root, parcel, 'EGB_Zmiana', 'podstawaUtworzeniaWersjiObiektu', 'nrZmiany')
        land_units = extract_namespace_ref(namespaces, root, parcel, 'EGB_JednostkaRejestrowaGruntow', 'JRG2', 'idJednostkiRejestrowej')
        addresses = extract_namespace_ref(namespaces, root, parcel, 'EGB_AdresNieruchomosci', 'adresDzialki', ['nazwaMiejscowosci', 'nazwaUlicy', 'numerPorzadkowy'])
        precincts = extract_namespace_ref(namespaces, root, parcel, 'EGB_ObrebEwidencyjny', 'lokalizacjaDzialki', ['idObrebu', 'nazwaWlasna'])
        registry_group_code = extract_namespace_ref(namespaces, root, parcel, 'EGB_JednostkaRejestrowaGruntow', 'JRG2', 'grupaRejestrowa')
        registry_group_code = int(registry_group_code[0]) if registry_group_code else None
        registry_group_label = f"{registry_group_code} [{group(registry_group_code)}]" if registry_group_code else None
        location_element = parcel.find('egb:lokalizacjaDzialki', namespaces=namespaces)
        precinct_ref = location_element.get('{http://www.w3.org/1999/xlink}href')
        precinct_element = root.find(f'.//egb:EGB_ObrebEwidencyjny[@gml:id="{precinct_ref.lstrip('#')}"]', namespaces=namespaces)
        location_precinct = precinct_element.find('egb:lokalizacjaObrebu', namespaces=namespaces)
        location_href = location_precinct.get('{http://www.w3.org/1999/xlink}href')
        admin_unit_element = root.find(f'.//egb:EGB_JednostkaEwidencyjna[@gml:id="{location_href.lstrip('#')}"]', namespaces=namespaces)
        admin_unit_id = admin_unit_element.findtext('egb:idJednostkiEwid', namespaces=namespaces)
        admin_unit_name = admin_unit_element.findtext('egb:nazwaWlasna', namespaces=namespaces)
        administrative_unit = f"{admin_unit_id} ({admin_unit_name})" if admin_unit_id and admin_unit_name else None
        buildings = root.findall('.//egb:EGB_Budynek', namespaces=namespaces)
        associated_buildings = [bld.findtext('egb:idBudynku', namespaces=namespaces) for bld in buildings if bld.find('egb:dzialkaZabudowana', namespaces=namespaces).get('{http://www.w3.org/1999/xlink}href') == parcel_id]

        owners = owner(root, namespaces, parcel)
        users = user(root, namespaces, parcel)

        land_classes = []
        for land_class in parcel.findall('.//egb:EGB_Klasouzytek', namespaces=namespaces):
            class_code = land_class.findtext('egb:OFU', namespaces=namespaces)
            subclass_code = land_class.findtext('egb:OZU', namespaces=namespaces)
            subclass_type = land_class.findtext('egb:OZK', namespaces=namespaces)
            class_area = land_class.find('egb:powierzchnia', namespaces=namespaces)
            class_area_value = class_area.text if class_area is not None else None
            class_area_unit = class_area.get('uom') if class_area is not None else None

            if subclass_type is None:
                land_classes.append(f"{class_code} {class_area_value} [{class_area_unit}]")
            else:
                land_classes.append(f"{class_code}/{subclass_code}{subclass_type} {class_area_value} [{class_area_unit}]")

        parcel_data = {
            'NAZWA KLASY': 'Działka Ewidencyjna',
            'IDENTYFIKATOR': identifier,
            'NR JEDN EWID': identifier[:8] if identifier else None,
            'NR OBRĘBU': identifier[9:13] if identifier else None,
            'NR DZIAŁKI': identifier[14:] if identifier else None,
            'KSIĘGA WIECZYSTA': land_register,
            'POWIERZCHNIA': f"{area} [{unit_of_measurement}]" if area else None,
            'KLASOUŻYTKI': " ".join(land_classes),
            'INFORMACJE': additional_info,
            'JEDN REJ GRUNTÓW': ", ".join(land_units),
            'GRUPA REJESTROWA': registry_group_label,
            'ADRESY': ", ".join(addresses),
            'BUDYNKI': ", ".join(associated_buildings),
            'WŁAŚCICIELE': ", ".join(owners),
            'WŁADAJĄCY': ", ".join(users),
            'LICZBA PUNKTÓW': boundary_point_count,
            'PUNKTY GRANICZNE': ", ".join(boundary_points),
            'OBRĘB': ", ".join(precincts),
            'JEDNOSTKA EWIDENCYJNA': administrative_unit,
            'OPERATY TECHNICZNE': ", ".join(tech_docs),
            'ZMIANA': ", ".join(modifications)
        }
        parcels.append(parcel_data)

    return parcels


root = etree.parse(select_file()).getroot()
nSP = {'gml': 'http://www.opengis.net/gml/3.2','egb': 'ewidencjaGruntowIBudynkow:1.0'}

polygon_namespaces = {
    'egb:EGB_JednostkaEwidencyjna':
        {'name': 'Jednostka Ewidencyjna', 'color': 'black', 'width': 3, 'label': 'nazwaWlasna'},
    'egb:EGB_ObrebEwidencyjny':
        {'name': 'Obręb Ewidencyjny', 'color': '#ff6600', 'width': 4, 'label': 'idObrebu'},
    'egb:EGB_KonturUzytkuGruntowego':
        {'name': 'Kontur Użytku Gruntowego', 'color': '#964B00', 'width': 2, 'label': 'OFU'},
    'egb:EGB_KonturKlasyfikacyjny':
        {'name': 'Kontur Klasyfikacyjny', 'color': '#33bb33', 'width': 2, 'label': ['OZU', 'OZK'] },
    'egb:EGB_DzialkaEwidencyjna':
        {'name': 'Dzialka Ewidencyjna', 'color': '#0066ff', 'width': 4, 'label': 'NR DZIAŁKI'},
    'egb:EGB_Budynek':
        {'name': 'Budynek', 'color': '#ff0000', 'width': 3, 'label': 'rodzajWgKST'},
    'egb:EGB_ObiektTrwaleZwiazanyZBudynkiem':
        {'name': 'Obiekt Trwale Związany z Budynkiem', 'color': 'black', 'width': 2}
}

points_namespaces = {
    'egb:EGB_PunktGraniczny':
        {'name': 'Punkt Graniczny', 'color': 'white', 'width': 5},
    'egb:EGB_AdresNieruchomosci':
        {'name': 'Adres Nieruchomości', 'color': '#ffff00', 'width': 10}
}

linestring_namespaces = {
    'egb:EGB_ObiektTrwaleZwiazanyZBudynkiem':
        {'name': 'Obiekt Trwale Związany z Budynkiem', 'color': '#ffa500', 'width': 3}
}

fig = go.Figure()

for polygon_ns, ns_info in polygon_namespaces.items():
    name = ns_info['name']
    color = ns_info['color']
    width = ns_info['width']
    label = ns_info.get('label', None)

    try:
        if name == 'Dzialka Ewidencyjna':
            attributes = extract_data(nSP)
        else:
            attributes = fetch_attributes(polygon_ns, nSP)
        polygons = polygon_from_gml(polygon_ns, nSP)
        polygons_df = transform_to_crs(polygons)

        shape_drawer(fig, polygons_df, name, attributes, color, width, label)

    except Exception as e:
        print(f"Error: {e}")

for point_ns, ns_info in points_namespaces.items():
    name =  ns_info['name']
    color = ns_info['color']
    width = ns_info['width']

    try:
        attributes = fetch_attributes(point_ns, nSP)
        points = [Point(float(coord[1]), float(coord[0]))
            for objec in root.findall(f".//{point_ns}", namespaces=nSP)
            if (pos := objec.find(".//gml:pos", namespaces=nSP)) is not None for coord in [pos.text.split()]]
        points_df = transform_to_crs(points)

        for i, (index, row) in enumerate(points_df.iterrows()):
            if isinstance(row.geometry, Point):
                x, y = row.geometry.xy
                serialized_attr = json.dumps(attributes[i], ensure_ascii=False)
                fig.add_trace(go.Scattermapbox(
                    lat=list(y), lon=list(x), mode='markers', marker=dict(size=width, color=color),
                    name=name, customdata=[serialized_attr] * len(x), hovertemplate="",
                    text=name, hoverinfo='text', legendgroup=name, showlegend=(i == 0)))

    except Exception as e:
        print(f"Error: {e}")

dzialki_ewidencyjne = polygon_from_gml("egb:EGB_DzialkaEwidencyjna", nSP)
dzialki_ewidencyjne_df = transform_to_crs(dzialki_ewidencyjne)
dzialki_ewidencyjne_df['NR_DZIALKI'] = [dzialka['NR DZIAŁKI'] for dzialka in extract_data(nSP)]

budynki = transform_to_crs(polygon_from_gml('egb:EGB_Budynek', nSP))
bounds = budynki.total_bounds

center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2
zoom = 16

fig.update_layout(
    mapbox=dict(style="carto-positron",
        center=dict(lat=center_lat, lon=center_lon),
        zoom=zoom,
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    mapbox_zoom=zoom,
    showlegend=True,
    legend_title=dict(
        text='Legenda',
        font=dict(size=20),
    ),
    legend=dict(
        itemclick="toggleothers",
        itemdoubleclick="toggle",
        orientation="h",
        x=1,
        y=0,
        xanchor='right',
        yanchor='bottom',
        borderwidth=4,
        bgcolor='rgba(0, 51, 102, 0.95)',
        font=dict(size=13, color='#dddddd', family='Courier New'),
    ),)

app = dash.Dash(__name__)
app.title = "Przeglądarka GML"

app.layout = html.Div([
    dcc.Store(id='stored-figure', data=fig.to_dict()),
    dcc.Store(id='stored-zoom', data={'center': {'lat': center_lat, 'lon': center_lon}, 'zoom': zoom}),

    html.Div([
        html.Div([
            dcc.Loading(
                overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                id='loading-table',
                type='dot',
                color="#fcd705",
                children=[
                    dash_table.DataTable(
                        id='table',
                        columns=[],
                        data=[],
                        style_table={
                            'overflowX': 'auto',
                            'maxHeight': '100vh',
                            'width': '100%',
                            'backgroundColor': 'rgba(0, 51, 102, 0.95)',
                            'border': '1px solid #ccc',
                            'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)',
                            'font-family': 'Courier New'
                        },
                        style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'color': 'white', 'backgroundColor': 'rgba(0, 51, 102, 0.95)', 'font-family': 'Courier New'},
                        style_header={'backgroundColor': 'rgba(0, 51, 102, 0.95)', 'fontWeight': 'bold', 'color': '#fcd705', 'font-family': 'Courier New'},
                    )])
        ], style={
            'width': '33.33%',
            'height': '100vh',
            'overflowY': 'auto',
            'backgroundColor': 'rgba(0, 51, 102, 1)',
            'padding': '10px',
            'boxShadow': '2px 0 5px rgba(0, 0, 0, 1)',
            'position': 'fixed',
            'left': 0,
            'top': 0,
            'bottom': 0,
            'zIndex': 1000
        }),

        html.Div([
            dcc.Loading(
                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                id='loading-map',
                type='dot',
                color="#fcd705",
                children=[
                    dcc.Graph(
                        id='map',
                        style={'height': '100vh', 'width': '100%'},
                        config={'scrollZoom': True, 'displayModeBar': False}
                    ),
                    html.Img(
                        src='/assets/compass.png',
                        style={
                            'position': 'absolute',
                            'top': '10px',
                            'right': '10px',
                            'width': '100px',
                            'opacity': 1,
                            'zIndex': 1001,
                        })])
        ], style={
            'marginLeft': '33.33%',
            'width': '66.66%',
            'height': '100vh',
            'position':'relative'
        })
    ], style={'display': 'flex', 'backgroundColor': 'black'}),
])

@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Output('map', 'figure'),
    Output('stored-zoom', 'data'),
    Input('map', 'clickData'),
    Input('stored-figure', 'data'),
    State('map', 'relayoutData'),
    State('stored-zoom', 'data')
)
def plot_attributes(clickData, stored_figure, relayoutData, stored_zoom):
    if clickData is None:
        return [], [], go.Figure(stored_figure), stored_zoom

    try:
        customdata = clickData['points'][0].get('customdata')
        if not customdata:
            print("No customdata found")
            return [], [], go.Figure(stored_figure), stored_zoom

        feature_data = json.loads(customdata[0] if isinstance(customdata, list) else customdata)
        flat_data = expand_keys(feature_data)
        filtered_data = {key: value for key, value in flat_data.items() if value is not None or value != ''}
        data = [{'Atrybut': key, 'Wartość atrybutu': value} for key, value in filtered_data.items()]
        columns = [{'name': 'Atrybut', 'id': 'Atrybut'}, {'name': 'Wartość atrybutu', 'id': 'Wartość atrybutu'}]

        if relayoutData and 'mapbox.center' in relayoutData and 'mapbox.zoom' in relayoutData:
            stored_zoom = {'center': relayoutData['mapbox.center'], 'zoom': relayoutData['mapbox.zoom']}

        fig = go.Figure(stored_figure)
        if 'NR DZIAŁKI' in filtered_data:
            parcel_number = filtered_data['NR DZIAŁKI'].strip()
            selected_parcel = dzialki_ewidencyjne_df[dzialki_ewidencyjne_df['NR_DZIALKI'] == parcel_number]
            if not selected_parcel.empty:
                x, y = selected_parcel.geometry.iloc[0].exterior.xy
                fig.add_trace(go.Scattermapbox(
                    lat=list(y),
                    lon=list(x),
                    mode='lines',
                    line=dict(width=6, color='aqua'),
                    name='Wybrana działka',
                    hoverinfo='skip'
                ))
            else:
                print("Parcel not found in dzialki_ewidencyjne_df")

        fig.update_layout(mapbox=dict(center=stored_zoom['center'], zoom=stored_zoom['zoom']))
        return columns, data, fig, stored_zoom

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error processing clickData: {e}")
        return [], [], go.Figure(stored_figure), stored_zoom

if __name__ == "__main__":
    app.run_server(debug=False, port=5000)


