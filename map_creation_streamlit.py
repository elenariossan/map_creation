import folium
import pandas as pd
import streamlit as st
from translate import Translator
import base64

# Charger les données depuis le fichier CSV
data = pd.read_csv('worldcities.csv')

def translate_to_english(name):
    translator = Translator(to_lang='en', from_lang='fr')
    translation = translator.translate(name)
    return translation

def agregar_marcadores_ciudades(mapa, ciudad_coord, icono_url, icon_size=(10, 10)):  
    icono = folium.CustomIcon(icono_url, icon_size=icon_size, icon_anchor=(5, 5))
    marcador_ciudad = folium.Marker(location=ciudad_coord, icon=icono).add_to(mapa)

def agregar_marcadores_y_rutas(mapa, ciudades, color_ruta, dash_array, weight):
    if dash_array == True:
        folium.PolyLine(ciudades, color=str(translate_to_english(color_ruta)), dash_array='5, 10', weight=weight).add_to(mapa)
    #folium.PolyLine(ciudades, color=color_ruta, dash_array='5, 10', weight=3).add_to(mapa)
    else:
        print("non point")
        folium.PolyLine(ciudades, color=str(translate_to_english(color_ruta)), weight = weight).add_to(mapa)

def get_coordinates(city_name):
    city = data[data['city_ascii'].str.lower() == city_name.lower()]
    if not city.empty:
        return city.iloc[0]['lat'], city.iloc[0]['lng']
    else:
        raise ValueError(f"Les coordonnées de '{city_name}' ne sont pas disponibles.")

class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def get_session_state():
    session_state = st.session_state.get('session_state')
    if session_state is None:
        session_state = SessionState(
            num_lines=1,
            cities={},
            colors={},
            icons={},
            connect_trajectories={},
            icon_size=(10, 10)  
        )
        st.session_state['session_state'] = session_state
    return session_state

def demander_villes_couleur_icone(key, session_state):
    villes_liste = data['city_ascii'].unique()
    ville_select = st.multiselect(f"Sélectionnez les villes ({key}):", villes_liste, key=f"villes_{key}")
    couleur_input = st.selectbox(f"Choisissez la couleur ({key}):", ('rouge', 'bleu', 'vert', 'noir', 'rose', 'gris', 'orange', 'jaune', 'violet'), key=f"couleur_{key}")

    
    icons_options = {
        "Broche de localisation": "https://icones.pro/wp-content/uploads/2021/02/icone-de-broche-de-localisation-{couleur_input}.png",
        "x": "https://icones.pro/wp-content/uploads/2022/05/icone-fermer-et-x-{couleur_input}.png",
        "Bus": "https://icones.pro/wp-content/uploads/2022/07/icone-de-bus-{couleur_input}.png"
    }
    

    icon_url = icons_options["x"].format(couleur_input=couleur_input)
    #selected_icon = st.radio("Sélectionnez un symbole :", list(icons_options.keys()), key=f"icon_{key}")
    #icon_url = icons_options[selected_icon].format(couleur_input=couleur_input)

    connect_traj = st.checkbox("Relier les trajets ?", key=f"connect_{key}")
    session_state.cities[key] = ville_select
    session_state.colors[str(key)] = couleur_input
    session_state.icons[str(key)] = icon_url
    session_state.connect_trajectories[key] = connect_traj

    dash_array = st.checkbox("Ligne en pointillés ?", key=f"pointilles_{key}")
    weight = st.slider("Epaisseur traits", 1.0, 6.0, step=0.1, format="%.1f", key=f"weight_{key}")


    return ville_select, couleur_input, connect_traj, session_state, dash_array, weight

def create_map_from_user_input(session_state):
    m = folium.Map(location=[43.6008335,1.2680296], zoom_start=5, tiles='CartoDB positron')

    for key in range(1, session_state.num_lines + 1):
        input_cities, couleur_fr, connect_traj, session_state, dash_array, weight = demander_villes_couleur_icone(str(key), session_state)
        city_coordinates = []
        for city_name in input_cities:
            try:
                coordinates = get_coordinates(city_name)
                city_coordinates.append(coordinates)
            except ValueError as e:
                st.error(e)
                st.error("Veuillez entrer des noms de villes valides.")
                return

        for coord in city_coordinates:
            icon_url = session_state.icons.get(str(key))
            if icon_url:
                agregar_marcadores_ciudades(m, coord, icon_url, session_state.icon_size)
            else:
                st.warning(f"Aucune icône trouvée pour la clé {key}")

        if connect_traj:
            for i in range(len(city_coordinates) - 1):
                if None not in city_coordinates[i:i+2]:
                    print(city_coordinates[i:i+2])
                    print(session_state.colors[str(key)])
                    print("dash_array")
                    print(dash_array)
                    agregar_marcadores_y_rutas(m, city_coordinates[i:i+2], session_state.colors[str(key)], dash_array, weight)

    st.markdown(get_table_download_link(m), unsafe_allow_html=True)

def get_table_download_link(m):
    html = m.get_root().render()
    b64 = base64.b64encode(html.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="carte_trajets.html">Télécharger la carte</a>'
    return href

st.title("Création de cartes")
session_state = get_session_state()
#st.write(session_state.icon_size)
#session_state.icon_size = st.sidebar.slider("Taille de l'icône", 1, 50)
#session_state.weight = st.sidebar.slider("Epaisseur traits", 1, 6)
session_state.num_lines = st.sidebar.slider("Nombre de lignes", 1, 30, session_state.num_lines)
create_map_from_user_input(session_state)
