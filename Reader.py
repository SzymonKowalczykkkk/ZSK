from lxml import etree
import json

xml_file = "zsk.xml"

# Parse the GML file
tree = etree.parse(xml_file)
root = tree.getroot()

# Define namespaces
ns = {
    'gml': 'http://www.opengis.net/gml/3.2',
    'egb': 'ewidencjaGruntowIBudynkow:1.0',
    'xlink': 'http://www.w3.org/1999/xlink'
}

def get_reference(ns, root, root_object, original, reference, name):
    # Find reference elements inside the root object
    references = root_object.findall(f'egb:{reference}', namespaces=ns)
    originals = root.findall(f'.//egb:{original}', namespaces=ns)

    names = []
    for ref in references:
        href = ref.get('{http://www.w3.org/1999/xlink}href')
        if not href:
            continue  

        href_id = href.lstrip('#') 

        for orgin in originals:
            gml_id = orgin.get('{http://www.opengis.net/gml/3.2}id')
            if gml_id == href_id:
                if isinstance(name, list):
                    # Extract multiple attributes safely
                    name_ref = [
                        orgin.findtext(f'egb:{n}', namespaces=ns) or ""
                        for n in name
                    ]
                    name_ref = " ".join(name_ref)
                else:
                    # Extract a single attribute
                    name_ref = orgin.findtext(f'egb:{name}', namespaces=ns) or ""

                names.append(name_ref)
    return names

def get_group_description(group_number):
    match group_number:
        case 1:
            return "Skarb Państwa, jeżeli nie występuje w zbiegu z użytkownikami wieczystymi"
        case 2:
            return "Skarb Państwa, jeżeli występuje w zbiegu z użytkownikami wieczystymi"
        case 3:
            return "jednoosobowe spółki Skarbu Państwa, przedsiębiorstwa państwowe i inne państwowe osoby prawne"
        case 4:
            return "gminy, związki międzygminne lub metropolitalne, jeżeli nie występują w zbiegu z użytkownikami wieczystymi"
        case 5:
            return "gminy, związki międzygminne lub metropolitalne, jeżeli występują w zbiegu z użytkownikami wieczystymi"
        case 6:
            return "jednoosobowe spółki jednostek samorządu terytorialnego i inne osoby prawne, których organami założycielskimi są organy samorządu terytorialnego"
        case 7:
            return "osoby fizyczne"
        case 8:
            return "spółdzielnie"
        case 9:
            return "kościoły i związki wyznaniowe"
        case 10:
            return "wspólnoty gruntowe"
        case 11:
            return "powiaty i związki powiatów, jeżeli nie występują w zbiegu z użytkownikami wieczystymi"
        case 12:
            return "powiaty i związki powiatów, jeżeli występują w zbiegu z użytkownikami wieczystymi"
        case 13:
            return "województwa, jeżeli nie występują w zbiegu z użytkownikami wieczystym."
        case 14:
            return "województwa, jeżeli występują w zbiegu z użytkownikami wieczystymi"
        case 15:
            return "spółki prawa handlowego"
        case 16:
            return "inne podmioty ewidencyjne"
        case _:
            return "Nieprawidłowy numer grupy. Podaj liczbę od 1 do 16."

def get_obiekt_trwale_type(type):
    match type:
        case "s":
            return "schody"
        case "r":
            return "rampa"
        case "o":
            return "podpora"
        case "t":
            return "taras"
        
    return "inny"

def extract_wlasciciele(root, ns, dzialka):
    wlasc = []
    jrg2_dzialka = dzialka.find('egb:JRG2', namespaces=ns)
    if jrg2_dzialka is not None:
        href_jrg2 = jrg2_dzialka.get('{http://www.w3.org/1999/xlink}href')
        wlasnosc = root.findall('.//egb:EGB_UdzialWeWlasnosci', namespaces=ns)
        
        for wl in wlasnosc:
            przedmiotUdzialuWlasnosci = wl.find('egb:przedmiotUdzialuWlasnosci', namespaces=ns)
            jednostkaRejestrowa = przedmiotUdzialuWlasnosci.find('egb:EGB_JednostkaRejestrowa', namespaces=ns)
            jrg_ref = jednostkaRejestrowa.find('egb:JRG', namespaces=ns)
            
            # Check if 'egb:JRG' exists
            if jrg_ref is not None:
                href_jrg2_wl = jrg_ref.get('{http://www.w3.org/1999/xlink}href')
                
                if href_jrg2 == href_jrg2_wl:
                    licznik = wl.findtext('egb:licznikUlamkaOkreslajacegoWartoscUdzialu', default="1", namespaces=ns)
                    mianownik = wl.findtext('egb:mianownikUlamkaOkreslajacegoWartoscUdzialu', default="1", namespaces=ns)
                    podmiotUdzialuWlasnosci = wl.find('egb:podmiotUdzialuWlasnosci', namespaces=ns)
                    podmiot = podmiotUdzialuWlasnosci.find('egb:EGB_Podmiot', namespaces=ns)
                    
                    wlasciciele = None
                    if podmiot is not None:
                        instytucja = podmiot.find('egb:instytucja1', namespaces=ns)
                        osoba_fizyczna = podmiot.find('egb:osobaFizyczna', namespaces=ns)
                        malzenstwo = podmiot.find('egb:malzenstwo', namespaces=ns)
                        
                        if instytucja is not None:
                            instytucja_href = instytucja.get('{http://www.w3.org/1999/xlink}href')
                            instytut = root.find(f'.//egb:EGB_Instytucja[@gml:id="{instytucja_href.lstrip("#")}"]', namespaces=ns)
                            nazwa = instytut.findtext('egb:nazwaPelna', default="", namespaces=ns)
                            adresInstytucji = instytut.find('egb:adresInstytucji', namespaces=ns)
                            adresInstytucji_href = adresInstytucji.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(f'.//egb:EGB_AdresZameldowania[@gml:id="{adresInstytucji_href.lstrip("#")}"]', namespaces=ns) 
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="", namespaces=ns)
                            
                            wlasciciele = f"[{licznik}/{mianownik}] [instytucja] {nazwa}, {miejscowosc} {kod_pocztowy} {ulica} {numerPorzadkowy}"

                        elif osoba_fizyczna is not None:
                            osob_href = osoba_fizyczna.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{osob_href.lstrip("#")}"]', namespaces=ns)
                            imie = osoba_fiz.findtext('egb:pierwszeImie', default="", namespaces=ns)
                            imie2 = osoba_fiz.findtext('egb:drugieImie', default="", namespaces=ns)
                            nazwisko = osoba_fiz.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                            ojciec = osoba_fiz.findtext('egb:imieOjca', default="", namespaces=ns)
                            matka = osoba_fiz.findtext('egb:imieMatki', default="", namespaces=ns)
                            adresOsobyFizycznej = osoba_fiz.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href = adresOsobyFizycznej.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href.lstrip("#")}"]', namespaces=ns)
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="", namespaces=ns)
                            
                            wlasciciele = f"[{licznik}/{mianownik}] [osoba fizyczna] {nazwisko} {imie} {imie2} ({ojciec} {matka}), {miejscowosc} {kod_pocztowy} {ulica} {numerPorzadkowy}"

                        elif malzenstwo is not None:
                            mal_href = malzenstwo.get('{http://www.w3.org/1999/xlink}href')
                            malzenstwo = root.find(f'.//egb:EGB_Malzenstwo[@gml:id="{mal_href.lstrip("#")}"]', namespaces=ns)
                            osoba1 = malzenstwo.find('egb:osobaFizyczna2', namespaces=ns)
                            os1_href = osoba1.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz1 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os1_href.lstrip("#")}"]', namespaces=ns)
                            osoba2 = malzenstwo.find('egb:osobaFizyczna3', namespaces=ns)
                            os2_href = osoba2.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz2 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os2_href.lstrip("#")}"]', namespaces=ns)

                            adresOsobyFizycznej = osoba_fiz1.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href = adresOsobyFizycznej.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href.lstrip("#")}"]', namespaces=ns)
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="", namespaces=ns)
                            
                            adresOsobyFizycznej2 = osoba_fiz2.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href2 = adresOsobyFizycznej2.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania2 = root.find(f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href2.lstrip("#")}"]', namespaces=ns)
                            miejscowosc2 = AdresZameldowania2.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy2 = AdresZameldowania2.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica2 = AdresZameldowania2.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy2 = AdresZameldowania2.findtext('egb:numerPorzadkowy', default="", namespaces=ns)
                            
                            if osoba1 is not None and osoba2 is not None:
                                imie1 = osoba_fiz1.findtext('egb:pierwszeImie', default="", namespaces=ns)
                                imie12 = osoba_fiz1.findtext('egb:drugieImie', default="", namespaces=ns)
                                ojciec1 = osoba_fiz1.findtext('egb:imieOjca', default="", namespaces=ns)
                                matka1 = osoba_fiz1.findtext('egb:imieMatki', default="", namespaces=ns)
                                nazwisko1 = osoba_fiz1.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                                
                                imie2 = osoba_fiz2.findtext('egb:pierwszeImie', default="", namespaces=ns)
                                imie22 = osoba_fiz2.findtext('egb:drugieImie', default="", namespaces=ns)
                                ojciec2 = osoba_fiz2.findtext('egb:imieOjca', default="", namespaces=ns)
                                matka2 = osoba_fiz2.findtext('egb:imieMatki', default="", namespaces=ns)
                                nazwisko2 = osoba_fiz2.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)

                                wlasciciele = (
                                    f"[{licznik}/{mianownik}] [małżeństwo] "
                                    f"{nazwisko1} {imie1} {imie12} ({ojciec1} {matka1}) i "
                                    f"{nazwisko2} {imie2} {imie22} ({ojciec2} {matka2})"
                                )

                    if wlasciciele:
                        wlasc.append(wlasciciele)
    return wlasc

def extract_wladajacy(root, ns, dzialka):
    wlasc = []
    jrg2_dzialka = dzialka.find('egb:JRG2', namespaces=ns)
    if jrg2_dzialka is not None:
        href_jrg2 = jrg2_dzialka.get('{http://www.w3.org/1999/xlink}href')
        wlasnosc = root.findall(f'.//egb:EGB_UdzialWeWladaniu', namespaces=ns)
        
        for wl in wlasnosc:
            przedmiotUdzialuWlasnosci = wl.find('egb:przedmiotUdzialuWladania', namespaces=ns)
            jednostkaRejestrowa = przedmiotUdzialuWlasnosci.find('egb:EGB_JednostkaRejestrowa', namespaces=ns)
            jrg_ref = jednostkaRejestrowa.find('egb:JRG', namespaces=ns)
            
            # Check if 'egb:JRG' exists
            if jrg_ref is not None:
                href_jrg2_wl = jrg_ref.get('{http://www.w3.org/1999/xlink}href')
                
                if href_jrg2 == href_jrg2_wl:
                    licznik = wl.findtext('egb:licznikUlamkaOkreslajacegoWartoscUdzialu', default="1", namespaces=ns)
                    mianownik = wl.findtext('egb:mianownikUlamkaOkreslajacegoWartoscUdzialu', default="1", namespaces=ns)
                    podmiotUdzialuWlasnosci = wl.find('egb:podmiotUdzialuWeWladaniu', namespaces=ns)
                    podmiot = podmiotUdzialuWlasnosci.find('egb:EGB_Podmiot', namespaces=ns)
                    
                    wlasciciele = None
                    if podmiot is not None:
                        instytucja = podmiot.find('egb:instytucja1', namespaces=ns)
                        osoba_fizyczna = podmiot.find('egb:osobaFizyczna', namespaces=ns)
                        malzenstwo = podmiot.find('egb:malzenstwo', namespaces=ns)
                        
                        if instytucja is not None:
                            instytucja_href = instytucja.get('{http://www.w3.org/1999/xlink}href')
                            instytut = root.find(f'.//egb:EGB_Instytucja[@gml:id="{instytucja_href.lstrip("#")}"]', namespaces=ns)
                            nazwa = instytut.findtext('egb:nazwaPelna', default="", namespaces=ns)
                            wlasciciele = f"[{licznik}/{mianownik}] [instytucja] {nazwa}"

                        elif osoba_fizyczna is not None:
                            osob_href = osoba_fizyczna.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{osob_href.lstrip("#")}"]', namespaces=ns)
                            imie = osoba_fiz.findtext('egb:pierwszeImie', default="", namespaces=ns)
                            imie2 = osoba_fiz.findtext('egb:drugieImie', default="", namespaces=ns)
                            nazwisko = osoba_fiz.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                            ojciec = osoba_fiz.findtext('egb:imieOjca', default="", namespaces=ns)
                            matka = osoba_fiz.findtext('egb:imieMatki', default="", namespaces=ns)
                            wlasciciele = f"[{licznik}/{mianownik}] [osoba fizyczna] {nazwisko} {imie} {imie2} ({ojciec} {matka})"

                        elif malzenstwo is not None:
                            mal_href = malzenstwo.get('{http://www.w3.org/1999/xlink}href')
                            malzenstwo = root.find(f'.//egb:EGB_Malzenstwo[@gml:id="{mal_href.lstrip("#")}"]', namespaces=ns)
                            osoba1 = malzenstwo.find('egb:osobaFizyczna2', namespaces=ns)
                            os1_href = osoba1.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz1 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os1_href.lstrip("#")}"]', namespaces=ns)
                            osoba2 = malzenstwo.find('egb:osobaFizyczna3', namespaces=ns)
                            os2_href = osoba2.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz2 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os2_href.lstrip("#")}"]', namespaces=ns)
                            
                            if osoba1 is not None and osoba2 is not None:
                                imie1 = osoba_fiz1.findtext('egb:pierwszeImie', default="", namespaces=ns)
                                imie12 = osoba_fiz1.findtext('egb:drugieImie', default="", namespaces=ns)
                                ojciec1 = osoba_fiz1.findtext('egb:imieOjca', default="", namespaces=ns)
                                matka1 = osoba_fiz1.findtext('egb:imieMatki', default="", namespaces=ns)
                                nazwisko1 = osoba_fiz1.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                                
                                imie2 = osoba_fiz2.findtext('egb:pierwszeImie', default="", namespaces=ns)
                                imie22 = osoba_fiz2.findtext('egb:drugieImie', default="", namespaces=ns)
                                ojciec2 = osoba_fiz2.findtext('egb:imieOjca', default="", namespaces=ns)
                                matka2 = osoba_fiz2.findtext('egb:imieMatki', default="", namespaces=ns)
                                nazwisko2 = osoba_fiz2.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)

                                wlasciciele = (
                                    f"[{licznik}/{mianownik}] [małżeństwo] "
                                    f"{nazwisko1} {imie1} {imie12} ({ojciec1} {matka1}) i "
                                    f"{nazwisko2} {imie2} {imie22} ({ojciec2} {matka2})"
                                )

                    if wlasciciele:
                        wlasc.append(wlasciciele)
    return wlasc

def read_egib(ns):
    dzialki = []
    # Iterate over each DzialkaEwidencyjna
    for dzialka in root.findall('.//egb:EGB_DzialkaEwidencyjna', namespaces=ns):
        id_dzialki = dzialka.get('{http://www.opengis.net/gml/3.2}id')
        identyfikator = dzialka.findtext('egb:idDzialki', namespaces=ns)
        numer_kw = dzialka.findtext('egb:numerKW', namespaces=ns)
        powierzchnia_elem = dzialka.find('egb:poleEwidencyjne', namespaces=ns)
        powierzchnia = powierzchnia_elem.text if powierzchnia_elem is not None else None
        uom = powierzchnia_elem.get('uom') if powierzchnia_elem is not None else None
        informacje = dzialka.findtext('egb:dodatkoweInformacje', namespaces=ns)


        operatory_techniczne = get_reference(ns, root, dzialka, 'EGB_OperatTechniczny', 'operatTechniczny2', 'identyfikatorOperatuWgPZGIK')
        punkty_graniczne = get_reference(ns, root, dzialka, 'EGB_PunktGraniczny', 'punktGranicyDzialki', 'idPunktu')
        liczba_puntkow = len(punkty_graniczne)
        zmiany = get_reference(ns, root, dzialka, 'EGB_Zmiana', 'podstawaUtworzeniaWersjiObiektu', 'nrZmiany')
        jrg = get_reference(ns, root, dzialka, 'EGB_JednostkaRejestrowaGruntow', 'JRG2', 'idJednostkiRejestrowej')
        adresy = get_reference(ns, root, dzialka, 'EGB_AdresNieruchomosci', 'adresDzialki', ['nazwaMiejscowosci', 'nazwaUlicy', 'numerPorzadkowy'])
        obreb = get_reference(ns, root, dzialka, 'EGB_ObrebEwidencyjny', 'lokalizacjaDzialki', ['idObrebu', 'nazwaWlasna'])
        grupa_rejestrowa = get_reference(ns, root, dzialka, 'EGB_JednostkaRejestrowaGruntow', 'JRG2', 'grupaRejestrowa')
        grupa_rejestrowa = int(grupa_rejestrowa[0])
        rejestr = f"{grupa_rejestrowa} [{get_group_description(grupa_rejestrowa)}]"

        # EGB_DzialkaEwidencyjna:lokalizacjaDzialki href == EGB_ObrebEwidencyjny gml:id, EGB_ObrebEwidencyjny:lokalizacjaObrebu href == jednostkEwidencyjna gml_id
        lokalizacjaDzialki = dzialka.find('egb:lokalizacjaDzialki', namespaces=ns)
        lokDzialki_href = lokalizacjaDzialki.get('{http://www.w3.org/1999/xlink}href')
        obreb_ewid = root.find(f'.//egb:EGB_ObrebEwidencyjny[@gml:id="{lokDzialki_href.lstrip("#")}"]', namespaces=ns)
        lokalizacjaObrebu = obreb_ewid.find(f'egb:lokalizacjaObrebu', namespaces=ns)
        lokObrebu_href = lokalizacjaObrebu.get('{http://www.w3.org/1999/xlink}href')
        jednostkEwidencyjna = root.find(f'.//egb:EGB_JednostkaEwidencyjna[@gml:id="{lokObrebu_href.lstrip("#")}"]', namespaces=ns)
        idJednostkiEwid = jednostkEwidencyjna.findtext('egb:idJednostkiEwid', namespaces=ns)
        nazwaWlasna = jednostkEwidencyjna.findtext('egb:nazwaWlasna', namespaces=ns)
        jednostka_ewidencyjna = f"{idJednostkiEwid} ({nazwaWlasna})"

        # EGB_Budynek:dzialkaZabudowana href == EGB_DzialkaEwidencyjna gml:id, idBudynku
        budynki = root.findall('.//egb:EGB_Budynek', namespaces=ns)
        id_budynkow = []
        for bud in budynki:
            dzialkaZabudowana = bud.find('egb:dzialkaZabudowana', namespaces=ns)
            dzialkaewid = dzialkaZabudowana.get('{http://www.w3.org/1999/xlink}href')
            idBudynku = bud.findtext('egb:idBudynku', namespaces=ns)
            if dzialkaewid == id_dzialki:
                id_budynkow.append(idBudynku)

        '''
        EGB_UdzialWeWladaniu, EGB_UdzialWeWlasnosci

        href 'JRG2' = href 'JRG2' w 'EGB_UdzialWeWlasnosci' 
        'EGB_Podmiot'- 'instytucja1' href = 'EGB_Instytucja' gml:id
        'EGB_Podmiot'- 'osobaFizyczna' href = 'EGB_OsobaFizyczna' gml:id
        'EGB_Podmiot'- 'malzenstwo' href = 'EGB_Malzenstwo' gml:id -  'EGB_OsobaFizyczna1', 'EGB_OsobaFizyczna2' 
        'pierwszyCzlonNazwiska' + 'pierwszeImie' + 'drugieImie' ('imieOjca' + 'imieMatki')
        '''

        wlasciciele = extract_wlasciciele(root, ns, dzialka)
        wladajacy = extract_wladajacy(root, ns, dzialka)

        # Extract klasouzytki
        klasouzytki = []
        for klasouzytek in dzialka.findall('.//egb:EGB_Klasouzytek', namespaces=ns):
            ofu = klasouzytek.findtext('egb:OFU', namespaces=ns)
            ozu = klasouzytek.findtext('egb:OZU', namespaces=ns)
            ozk = klasouzytek.findtext('egb:OZK', namespaces=ns)
            pow_elem = klasouzytek.find('egb:powierzchnia', namespaces=ns)
            pow_value = pow_elem.text if pow_elem is not None else None
            pow_unit = pow_elem.get('uom') if pow_elem is not None else None

            if ozk is None:
                klasouzytki.append(
                    f"{ofu} {pow_value} [{pow_unit}]"
                )
            else:
                klasouzytki.append(
                    f"{ofu}/{ozu}{ozk} {pow_value} [{pow_unit}]"
                )

        dzialka_data = {
            'NAZWA KLASY': 'Działka Ewidencyjna',
            'IDENTYFIKATOR': identyfikator,
            'NR JEDN EWID': identyfikator[:8] if identyfikator else None,
            'NR OBRĘBU': identyfikator[9:13] if identyfikator else None,
            'NR DZIAŁKI': identyfikator[14:] if identyfikator else None,
            'KSIĘGA WIECZYSTA': numer_kw,
            'POWIERZCHNIA': f"{powierzchnia} [{uom}]" if powierzchnia else None,
            'KLASOUŻYTKI': " ".join(klasouzytki),
            'INFORMACJE': informacje,
            'JEDN REJ GRUNTÓW': ", ".join(jrg),
            'GRUPA REJESTROWA': rejestr,
            'ADRESY': ", ".join(adresy),
            'BUDYNKI': ", ".join(id_budynkow),
            'WŁAŚCICIELE': ", ".join(wlasciciele),
            'WŁADAJĄCY': ", ".join(wladajacy),
            'LICZBA PUNKTÓW': liczba_puntkow,
            'PUNKTY GRANICZNE': ", ".join(punkty_graniczne),
            'OBRĘB': ", ".join(obreb),
            'JEDNOSTKA EWIDENCYJNA': jednostka_ewidencyjna,
            'OPERATY TECHNICZNE': ", ".join(operatory_techniczne),
            'ZMIANA': ", ".join(zmiany)
        }

        dzialki.append(dzialka_data)

    return dzialki
