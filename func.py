
def group(group_number):
    descriptions = {
        1: "Skarb Państwa, jeżeli nie występuje w zbiegu z użytkownikami wieczystymi",
        2: "Skarb Państwa, jeżeli występuje w zbiegu z użytkownikami wieczystymi",
        3: "jednoosobowe spółki Skarbu Państwa, przedsiębiorstwa państwowe i inne państwowe osoby prawne",
        4: "gminy, związki międzygminne lub metropolitalne, jeżeli nie występują w zbiegu z użytkownikami wieczystymi",
        5: "gminy, związki międzygminne lub metropolitalne, jeżeli występują w zbiegu z użytkownikami wieczystymi",
        6: "jednoosobowe spółki jednostek samorządu terytorialnego i inne osoby prawne, których organami założycielskimi są organy samorządu terytorialnego",
        7: "osoby fizyczne",
        8: "spółdzielnie",
        9: "kościoły i związki wyznaniowe",
        10: "wspólnoty gruntowe",
        11: "powiaty i związki powiatów, jeżeli nie występują w zbiegu z użytkownikami wieczystymi",
        12: "powiaty i związki powiatów, jeżeli występują w zbiegu z użytkownikami wieczystymi",
        13: "województwa, jeżeli nie występują w zbiegu z użytkownikami wieczystym.",
        14: "województwa, jeżeli występują w zbiegu z użytkownikami wieczystymi",
        15: "spółki prawa handlowego",
        16: "inne podmioty ewidencyjne"
    }
    return descriptions.get(group_number)


def owner(root, ns, dzialka):
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
                    mianownik = wl.findtext('egb:mianownikUlamkaOkreslajacegoWartoscUdzialu', default="1",
                                            namespaces=ns)
                    podmiotUdzialuWlasnosci = wl.find('egb:podmiotUdzialuWlasnosci', namespaces=ns)
                    podmiot = podmiotUdzialuWlasnosci.find('egb:EGB_Podmiot', namespaces=ns)

                    wlasciciele = None
                    if podmiot is not None:
                        instytucja = podmiot.find('egb:instytucja1', namespaces=ns)
                        osoba_fizyczna = podmiot.find('egb:osobaFizyczna', namespaces=ns)
                        malzenstwo = podmiot.find('egb:malzenstwo', namespaces=ns)

                        if instytucja is not None:
                            instytucja_href = instytucja.get('{http://www.w3.org/1999/xlink}href')
                            instytut = root.find(f'.//egb:EGB_Instytucja[@gml:id="{instytucja_href.lstrip("#")}"]',
                                                 namespaces=ns)
                            nazwa = instytut.findtext('egb:nazwaPelna', default="", namespaces=ns)
                            adresInstytucji = instytut.find('egb:adresInstytucji', namespaces=ns)
                            adresInstytucji_href = adresInstytucji.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(
                                f'.//egb:EGB_AdresZameldowania[@gml:id="{adresInstytucji_href.lstrip("#")}"]',
                                namespaces=ns)
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="",
                                                                         namespaces=ns)

                            wlasciciele = f"[{licznik}/{mianownik}] [instytucja] {nazwa}, {miejscowosc} {kod_pocztowy} {ulica} {numerPorzadkowy}"

                        elif osoba_fizyczna is not None:
                            osob_href = osoba_fizyczna.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{osob_href.lstrip("#")}"]',
                                                  namespaces=ns)
                            imie = osoba_fiz.findtext('egb:pierwszeImie', default="", namespaces=ns)
                            imie2 = osoba_fiz.findtext('egb:drugieImie', default="", namespaces=ns)
                            nazwisko = osoba_fiz.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                            ojciec = osoba_fiz.findtext('egb:imieOjca', default="", namespaces=ns)
                            matka = osoba_fiz.findtext('egb:imieMatki', default="", namespaces=ns)
                            adresOsobyFizycznej = osoba_fiz.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href = adresOsobyFizycznej.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(
                                f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href.lstrip("#")}"]',
                                namespaces=ns)
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="",
                                                                         namespaces=ns)

                            wlasciciele = f"[{licznik}/{mianownik}] [osoba fizyczna] {nazwisko} {imie} {imie2} ({ojciec} {matka}), {miejscowosc} {kod_pocztowy} {ulica} {numerPorzadkowy}"

                        elif malzenstwo is not None:
                            mal_href = malzenstwo.get('{http://www.w3.org/1999/xlink}href')
                            malzenstwo = root.find(f'.//egb:EGB_Malzenstwo[@gml:id="{mal_href.lstrip("#")}"]',
                                                   namespaces=ns)
                            osoba1 = malzenstwo.find('egb:osobaFizyczna2', namespaces=ns)
                            os1_href = osoba1.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz1 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os1_href.lstrip("#")}"]',
                                                   namespaces=ns)
                            osoba2 = malzenstwo.find('egb:osobaFizyczna3', namespaces=ns)
                            os2_href = osoba2.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz2 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os2_href.lstrip("#")}"]',
                                                   namespaces=ns)

                            adresOsobyFizycznej = osoba_fiz1.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href = adresOsobyFizycznej.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania = root.find(
                                f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href.lstrip("#")}"]',
                                namespaces=ns)
                            miejscowosc = AdresZameldowania.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy = AdresZameldowania.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica = AdresZameldowania.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy = AdresZameldowania.findtext('egb:numerPorzadkowy', default="",
                                                                         namespaces=ns)

                            adresOsobyFizycznej2 = osoba_fiz2.find('egb:adresOsobyFizycznej', namespaces=ns)
                            adresOsobyFizycznej_href2 = adresOsobyFizycznej2.get('{http://www.w3.org/1999/xlink}href')
                            AdresZameldowania2 = root.find(
                                f'.//egb:EGB_AdresZameldowania[@gml:id="{adresOsobyFizycznej_href2.lstrip("#")}"]',
                                namespaces=ns)
                            miejscowosc2 = AdresZameldowania2.findtext('egb:miejscowosc', default="", namespaces=ns)
                            kod_pocztowy2 = AdresZameldowania2.findtext('egb:kodPocztowy', default="", namespaces=ns)
                            ulica2 = AdresZameldowania2.findtext('egb:ulica', default="", namespaces=ns)
                            numerPorzadkowy2 = AdresZameldowania2.findtext('egb:numerPorzadkowy', default="",
                                                                           namespaces=ns)

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


def user(root, ns, dzialka):
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
                    mianownik = wl.findtext('egb:mianownikUlamkaOkreslajacegoWartoscUdzialu', default="1",
                                            namespaces=ns)
                    podmiotUdzialuWlasnosci = wl.find('egb:podmiotUdzialuWeWladaniu', namespaces=ns)
                    podmiot = podmiotUdzialuWlasnosci.find('egb:EGB_Podmiot', namespaces=ns)

                    wlasciciele = None
                    if podmiot is not None:
                        instytucja = podmiot.find('egb:instytucja1', namespaces=ns)
                        osoba_fizyczna = podmiot.find('egb:osobaFizyczna', namespaces=ns)
                        malzenstwo = podmiot.find('egb:malzenstwo', namespaces=ns)

                        if instytucja is not None:
                            instytucja_href = instytucja.get('{http://www.w3.org/1999/xlink}href')
                            instytut = root.find(f'.//egb:EGB_Instytucja[@gml:id="{instytucja_href.lstrip("#")}"]',
                                                 namespaces=ns)
                            nazwa = instytut.findtext('egb:nazwaPelna', default="", namespaces=ns)
                            wlasciciele = f"[{licznik}/{mianownik}] [instytucja] {nazwa}"

                        elif osoba_fizyczna is not None:
                            osob_href = osoba_fizyczna.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{osob_href.lstrip("#")}"]',
                                                  namespaces=ns)
                            imie = osoba_fiz.findtext('egb:pierwszeImie', default="", namespaces=ns)
                            imie2 = osoba_fiz.findtext('egb:drugieImie', default="", namespaces=ns)
                            nazwisko = osoba_fiz.findtext('egb:pierwszyCzlonNazwiska', default="", namespaces=ns)
                            ojciec = osoba_fiz.findtext('egb:imieOjca', default="", namespaces=ns)
                            matka = osoba_fiz.findtext('egb:imieMatki', default="", namespaces=ns)
                            wlasciciele = f"[{licznik}/{mianownik}] [osoba fizyczna] {nazwisko} {imie} {imie2} ({ojciec} {matka})"

                        elif malzenstwo is not None:
                            mal_href = malzenstwo.get('{http://www.w3.org/1999/xlink}href')
                            malzenstwo = root.find(f'.//egb:EGB_Malzenstwo[@gml:id="{mal_href.lstrip("#")}"]',
                                                   namespaces=ns)
                            osoba1 = malzenstwo.find('egb:osobaFizyczna2', namespaces=ns)
                            os1_href = osoba1.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz1 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os1_href.lstrip("#")}"]',
                                                   namespaces=ns)
                            osoba2 = malzenstwo.find('egb:osobaFizyczna3', namespaces=ns)
                            os2_href = osoba2.get('{http://www.w3.org/1999/xlink}href')
                            osoba_fiz2 = root.find(f'.//egb:EGB_OsobaFizyczna[@gml:id="{os2_href.lstrip("#")}"]',
                                                   namespaces=ns)

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
