from Reader import read_egib
from shapely.geometry import Point, Polygon, LineString
import geopandas as gpd
from lxml import etree
import json
from dash import dcc, html, dash_table, Input, Output, callback
import dash
import plotly.graph_objects as go

# Parse the GML file
etreeObj = etree.parse("zsk.xml")
root = etreeObj.getroot()

# Namespace for GML and EGIB
nSP = {
    'gml': 'http://www.opengis.net/gml/3.2',
    'egb': 'ewidencjaGruntowIBudynkow:1.0'
}

def getAttr(objName, nSP):
    ignored_attributes = ['startObiekt', 'startWersjaObiekt', 'EGB_IdentyfikatorIIP']
    def recursive_extract(element):
        attributes = {}
        for child in element:
            tag = etree.QName(child.tag).localname
 
            if tag.lower() in ['geometria']:
                continue
 
            if tag in ignored_attributes:
                continue
 
            if len(child):
                nested_attributes = recursive_extract(child)
                if nested_attributes:
                    attributes[tag] = nested_attributes
            else:
                value = child.text.strip() if child.text else None
                if value is not None:
                    attributes[tag] = value
        return attributes
 
    attributes_list = []
    for obj in root.findall(f".//{objName}", namespaces=nSP):
        extracted_attributes = recursive_extract(obj)
        if extracted_attributes:
            if objName in points_namespaces:
                pos = obj.find(".//gml:pos", namespaces=nSP)
                if pos is not None:
                    extracted_attributes['pos'] = pos.text.strip()
            attributes_list.append(extracted_attributes)
 
    return attributes_list


def flatten_attributes(attributes, parent_key=''):
    items = []
    for key, value in attributes.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            items.extend(flatten_attributes(value, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def format_hover_text(attributes):
    if not isinstance(attributes, dict):
        raise ValueError(f"Expected a dictionary for attributes, got {type(attributes)}")
    return "<br>".join(f"{key}: {value}" for key, value in attributes.items() if value is not None)


# finds all polygons in the provided namespace
def extract_polygon(object_name, ns):
    polygons = []
    for obj in root.findall(f".//{object_name}", namespaces=ns):
        exterior = obj.find(".//gml:exterior", namespaces=ns)
        if exterior is not None:
            coords = exterior.find(".//gml:posList", namespaces=ns).text
            coords = [float(c) for c in coords.split()]
            coords = [(coords[i+1], coords[i]) for i in range(0, len(coords), 2)]
            polygons.append(Polygon(coords))
    
    return polygons

def extract_points(object_name, ns):
    points = []
    coords = []
    for objec in root.findall(f".//{object_name}", namespaces=ns):
        pos = objec.find(".//gml:pos", namespaces=ns)
        if pos is not None:
            coords = [float(c) for c in pos.text.split()]
            points.append(Point(coords[1], coords[0]))

    return points

def extract_linestring(object_name, ns):
    linestrings = []
    for objec in root.findall(object_name, namespaces=ns):
        pos_list = objec.find(".//gml:posList", namespaces=ns)
        if pos_list is not None:
            coords = [float(c) for c in pos_list.text.split()]
            coords = [(coords[i+1], coords[i]) for i in range(0, len(coords), 2)]
            linestrings.append(LineString(coords))

    return linestrings

# transform polygons to GeoDataFrame and change crs to 4326 (visualisation reasons)
def polygon2df4326(polygons):
    polygon_gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:2178")
    polygon_gdf = polygon_gdf.to_crs(epsg=4326)

    return polygon_gdf

# transform points to GeoDataFrame and change crs to 4326 (visualisation reasons)
def point2df4326(points):
    point_gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:2178")
    point_gdf = point_gdf.to_crs(epsg=4326)

    return point_gdf

def linestring2df4326(linestrings):
    linestring_gdf = gpd.GeoDataFrame(geometry=linestrings, crs="EPSG:2178")
    linestring_gdf = linestring_gdf.to_crs(epsg=4326)
 
    return linestring_gdf

# plots polygons on the map
def plot_polygons(fig, dataframe, group_name, attributes, color, width, label):
    for i, row in dataframe.iterrows():
        if isinstance(row.geometry, Polygon):
            x, y = row.geometry.exterior.xy
            attribute = attributes[i]
            serialized_attr = json.dumps(attribute, ensure_ascii=False)

            if isinstance(label, list):
                label_value = " ".join([attribute.get(l, None) for l in label])
            else:
                label_value = attribute.get(label, None)

            fig.add_trace(go.Scattermapbox(
                lat=list(y),
                lon=list(x),
                mode='lines',
                line=dict(width=width, color=color),
                name=group_name,
                customdata=[serialized_attr]*len(x),
                hovertemplate="",
                text=group_name,
                hoverinfo='text',
                legendgroup=group_name,
                showlegend=(i == 0)
            ))

            # add labels in the centroid of each polygon
            centroid = row.geometry.centroid
            fig.add_trace(go.Scattermapbox(
                lat=[centroid.y],
                lon=[centroid.x],
                mode='text',
                name=label_value,
                customdata=[serialized_attr] * len(x),
                text=label_value,
                textfont=dict(size=10, color=color),
                showlegend=False,
                hoverinfo='text',
                legendgroup=group_name
            ))

def plot_points(fig, dataframe, group_name, attributes, color, width):
    for i, row in dataframe.iterrows():
        if isinstance(row.geometry, Point):
            x, y = row.geometry.xy
            attribute = attributes[i]
            serialized_attr = json.dumps(attribute, ensure_ascii=False)
            
            fig.add_trace(go.Scattermapbox(
                lat=list(y),
                lon=list(x),
                mode='markers',
                marker=dict(size=width, color=color),
                name=group_name,
                customdata=[serialized_attr] * len(x),
                hovertemplate="",
                text=group_name,
                hoverinfo='text',
                legendgroup=group_name,
                showlegend=(i == 0)
            ))


def plot_linestrings(fig, dataframe, group_name, attributes, color, width):
    for i, row in dataframe.iterrows():
        if isinstance(row.geometry, LineString):
            x, y = row.geometry.xy
            attribute = attributes[i]
            serialized_attr = json.dumps(attribute, ensure_ascii = False)

            fig.add_trace(go.Scattermapbox(
                lat=list(y),
                lon=list(x),
                mode='lines',
                line=dict(width=width, color=color),
                name=group_name,
                customdata=[serialized_attr]*len(x),
                hovertemplate="",
                text=group_name,
                hoverinfo='text',
                legendgroup=group_name,
                showlegend=(i == 0)
            ))


polygon_namespaces = {
    'egb:EGB_JednostkaEwidencyjna':
        {
            'name': 'Jednostka Ewidencyjna',
            'color': 'black',
            'width': 3,
            'label': 'nazwaWlasna'
        },
    'egb:EGB_ObrebEwidencyjny':
        {
            'name': 'Obręb Ewidencyjny',
            'color': '#ff00ff',
            'width': 4,
            'label': 'idObrebu'
        },
    'egb:EGB_KonturUzytkuGruntowego':
        {
            'name': 'Kontur Użytku Gruntowego',
            'color': '#964B00',
            'width': 2,
            'label': 'OFU'
        },
    'egb:EGB_KonturKlasyfikacyjny':
        {
            'name': 'Kontur Klasyfikacyjny',
            'color': '#33bb33',
            'width': 2,
            'label': ['OZU', 'OZK']
        },
    'egb:EGB_DzialkaEwidencyjna':
        {
            'name': 'Dzialka Ewidencyjna',
            'color': '#0000ff',
            'width': 4,
            'label': 'NR DZIAŁKI'
        },
    'egb:EGB_Budynek':
        {
            'name': 'Budynek',
            'color': '#ff0000',
            'width': 3,
            'label': 'rodzajWgKST'
        },
    'egb:EGB_ObiektTrwaleZwiazanyZBudynkiem':
        {
            'name': 'Obiekt Trwale Związany z Budynkiem',
            'color': 'black',
            'width': 2        
        }
}

points_namespaces = {
    'egb:EGB_PunktGraniczny':
    {
        'name': 'Punkt Graniczny',
        'color': 'white',
        'width': 5
    },
    'egb:EGB_AdresNieruchomosci':
    {
        'name': 'Adres Nieruchomości',
        'color': '#ffff00',
        'width': 10
    }
}

linestring_namespaces = {
    'egb:EGB_ObiektTrwaleZwiazanyZBudynkiem': {
        'name': 'Obiekt Trwale Związany z Budynkiem',
        'color': '#ffa500',
        'width': 3
    }
}

# Create a Plotly figure
fig = go.Figure()

# Extract and plot polygon objects
for polygon_ns, ns_info in polygon_namespaces.items():
    name = ns_info['name']
    color = ns_info['color']
    width = ns_info['width']
    label = ns_info.get('label', None)

    try:
        if name == 'Dzialka Ewidencyjna':
            attributes = read_egib(nSP)
        else:
            attributes = getAttr(polygon_ns, nSP)
        polygons = extract_polygon(polygon_ns, nSP)
        polygons_df = polygon2df4326(polygons)

        plot_polygons(fig, polygons_df, name, attributes, color, width, label)

    except Exception as e:
        print(f"Error: {e}")

# Extract and plot point objects
for point_ns, ns_info in points_namespaces.items():
    name =  ns_info['name']
    color = ns_info['color']
    width = ns_info['width']

    try:
        attributes = getAttr(point_ns, nSP)
        points = extract_points(point_ns, nSP)
        points_df = point2df4326(points)

        plot_points(fig, points_df, name, attributes, color, width)

    except Exception as e:
        print(f"Error: {e}")

# calculate bounding box for auto zoom
dzialki_ewidencyjne = extract_polygon("egb:EGB_DzialkaEwidencyjna", nSP)
dzialki_ewidencyjne_df = polygon2df4326(dzialki_ewidencyjne)

bounds = dzialki_ewidencyjne_df.total_bounds

center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2
zoom = 16

# map style
fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(lat=center_lat, lon=center_lon),
        zoom=zoom,
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    mapbox_zoom=zoom,
    showlegend=True,
    legend_title=dict(
        text='~ EGIB ~'
    ),
    legend=dict(
        orientation="v",
        x=1,
        y=0,
        xanchor='right',
        yanchor='bottom',
        bgcolor='rgba(100, 100, 0, 0.95)',
        font=dict(size=13, color='#dddddd', family='Courier New'),
    ),
)

app = dash.Dash(__name__)
app.title = "Przeglądarka EGIB"

app.layout = html.Div([
    dcc.Store(id='stored-figure', data=fig.to_dict()),

    html.Div([
        # Left column for displaying information
        html.Div([
            dash_table.DataTable(
                id='table',
                columns=[],
                data=[],
                style_table={
                    'overflowX': 'auto',
                    'maxHeight': '100vh',
                    'width': '100%',
                    'backgroundColor': 'rgba(100, 100, 0, 0.95)',
                    'border': '1px solid #ccc',
                    'boxShadow': '2px 2px 10px rgba(0, 0, 0, 0.1)',
                    'font-family': 'Courier New'
                },
                style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'color': 'white', 'backgroundColor': 'rgba(100, 100, 0, 0.95)', 'font-family': 'Courier New'},
                style_header={'backgroundColor': 'rgba(30, 30, 0, 1)', 'fontWeight': 'bold', 'color': 'yellow', 'font-family': 'Courier New'},
            )
        ], style={
            'width': '33.33%',
            'height': '100vh',
            'overflowY': 'auto',
            'backgroundColor': 'rgba(70, 70, 0, 1)',
            'padding': '10px',
            'boxShadow': '2px 0 5px rgba(0, 0, 0, 1)',
            'position': 'fixed',
            'left': 0,
            'top': 0,
            'bottom': 0,
            'zIndex': 1000
        }),

        # Right column for the map
        html.Div([
            dcc.Graph(
                id='map',
                style={'height': '100vh', 'width': '100%'},
                config={'scrollZoom': True, 'displayModeBar': False}    # False can be changed to True
            ),
            html.Img(
            src='/assets/compass.png',  # Replace with your image URL
            style={
                'position': 'absolute',
                'top': '10px',  # Adjust as needed
                'right': '10px',  # Adjust as needed
                'width': '100px',  # Specify the width
                # 'height': '50px',  # Specify the height
                'opacity': 1,
                'zIndex': 1001,  # Ensure the image is in front of other elements
            }
        )
        ], style={
            'marginLeft': '33.33%',
            'width': '66.66%',
            'height': '100vh'
        })
    ], style={'display': 'flex', 'backgroundColor': 'black'}),
])

@app.callback(
    Output('map', 'figure'),
    Input('stored-figure', 'data')
)
def load_static_map(stored_figure):
    return go.Figure(stored_figure)

# Callback to displat the table
@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('map', 'clickData')
)
def display_attributes(clickData):
    if clickData is None:
        return [], []

    try:
        customdata = clickData['points'][0].get('customdata')
        if not customdata:
            print("No customdata found")
            return [], []

        # Deserialize customdata (ensure it's properly formatted JSON)
        feature_data = json.loads(customdata[0] if isinstance(customdata, list) else customdata)

        # Flatten nested attributes
        flat_data = flatten_attributes(feature_data)

        # Filter out attributes with None values
        filtered_data = {key: value for key, value in flat_data.items() if value is not None or value != ''}

        # Prepare data for the DataTable
        data = [{'Atrybut': key, 'Wartość': value} for key, value in filtered_data.items()]
        columns = [
            {'name': 'Atrybut', 'id': 'Atrybut'},
            {'name': 'Wartość', 'id': 'Wartość'}
        ]

        return columns, data

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error processing clickData: {e}")
        return [], []


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True, port=5000)


