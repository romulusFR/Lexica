"""_summary_

Returns:
    _type_: _description_
"""
import os
import json
import urllib.parse
import psycopg

from dotenv import dotenv_values
from tqdm import tqdm

os.chdir(os.path.dirname(__file__))

if os.path.exists(".env"):
    config = dotenv_values(".env")
else:
    config = dotenv_values("default.env")


FILENAME_DB_SHEMA = "database/database.sql"
FILENAME_FUNCTION_SHEMA = "database/function.sql"
options = urllib.parse.quote_plus("--search_path=modern,public")
CONN_PARAMS = f"postgresql://{config['USER']}:{config['PASSWORD']}@{config['HOST']}:{config['PORT']}/{config['DATABASE']}?options={options}"  # pylint: disable=line-too-long


def update_function():  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            with open(FILENAME_FUNCTION_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())


def reset_table():  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            with open(FILENAME_DB_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())
            with open(FILENAME_FUNCTION_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())


def add_langue(cur, langue, livre):  # pylint: disable=missing-function-docstring
    cur.execute(
        "INSERT INTO langue (nom_langue) VALUES (%(langue)s);", {"langue": langue}
    )
    cur.execute(
        """INSERT INTO langue_dans_un_livre (id_livre,id_langue)
        VALUES (get_id_livre(%(livre)s),get_id_langue(%(langue)s));""",
        {"langue": langue, "livre": livre},
    )


def hienghene_process(
    cur, line, livre, liste_langue, count
):  # pylint: disable=missing-function-docstring
    liste_line = line.split(";")
    num_page = liste_line[len(liste_line) - 1]
    del liste_line[len(liste_line) - 1]
    requete = "INSERT INTO data (id_langue , sens , traduction , numero_page,id_livre) VALUES "
    for langue, element in zip(liste_langue, liste_line):
        # try:
        #     json_obj = json.loads(element)
        #     mots = json_obj["text"]
        #     if mots != "":
        #         mots = mots.replace("'", "''")
        #         requete += f"""
        #         ((select get_id_langue('{langue}')),'{count}','{mots}','{num_page}',(select get_id_livre('{livre}'))),"""
        #         # ST_MakeEnvelope({element["coord"]["x"]}, {element["coord"]["y"]}, {element["coord"]["x2"]}, {element["coord"]["y2"]})))), pylint: disable=line-too-long

        # except:
        #     pass
        if element != "":
            element = element.replace("'", "''")
            requete += f"""
                ((select get_id_langue('{langue}')),'{count}','{element}','{num_page}',(select get_id_livre('{livre}'))),"""

    requete = requete[0 : len(requete) - 1] + ";"
    cur.execute(requete)


def modif_data(langue, text, sens):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO data (id_langue , sens , traduction , numero_page,id_livre)
                        VALUES((select get_id_langue(%(langue)s)),%(sens)s,%(text)s,
                        (SELECT DISTINCT numero_page FROM data where sens=%(sens)s),
                        (SELECT DISTINCT id_livre FROM data where sens=%(sens)s))""",
                {
                    "langue": langue,
                    "text": text,
                    "sens": sens,
                },
            )


def search(
    keyword, engine, langue, langue_base, offset
):  # pylint: disable=missing-function-docstring

    res = []
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            # argument a la place {} ~ a la place de like
            # https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-POSIX-REGEXP
            # enfin https://www.postgresql.org/docs/current/pgtrgm.html
            # peut etre https://www.postgresql.org/docs/current/fuzzystrmatch.html
            # apres https://www.postgresql.org/docs/current/textsearch.html

            # * TSQUERY

            # * METAPHONE
            # cur.execute(
            #     """
            #     SELECT DISTINCT count(sens) FROM dataid_langue=
            #         WHERE dmetaphone(traduction) = dmetaphone(%(keyword)s)
            #         AND id_langue=(select get_id_langue(%(langueBase)s))""",
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #     },
            # )
            # count = cur.fetchone()[0]
            # print(count)
            # cur.execute(
            #     """
            #     SELECT DISTINCT sens FROM data
            #         WHERE dmetaphone(traduction) = dmetaphone(%(keyword)s)
            #         AND id_langue=(select get_id_langue(%(langueBase)s))
            #         ORDER BY sens
            #         LIMIT 25
            #         OFFSET %(offset)s;
            #         """,
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #         "offset": offset,
            #     },
            # )

            # * SIMILARITY
            # cur.execute(
            #     """
            #     SELECT DISTINCT count(sens) FROM data
            #         WHERE similarity(traduction,%(keyword)s) > 0.3
            #         AND id_langue=(select get_id_langue(%(langueBase)s))""",
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #     },
            # )
            # count = cur.fetchone()[0]
            # print(count)
            # cur.execute(
            #     """
            #     SELECT sens,similarity(traduction,%(keyword)s),nom_langue FROM data
            #         WHERE similarity(traduction,%(keyword)s) > 0.3
            #         AND id_langue=(select get_id_langue(%(langueBase)s))
            #         ORDER BY sens
            #         LIMIT 25
            #         OFFSET %(offset)s;
            #         """,
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #         "offset": offset,
            #     },
            # )
            cur.execute(
                "SELECT get_count_by_engine(%(keyword)s,%(engine)s,%(langue_base)s)",
                {
                    "keyword": keyword,
                    "engine": engine,
                    "langue_base": langue_base,
                },
            )
            count = cur.fetchone()[0]

            cur.execute(
                "Select * from search(%(keyword)s,%(engine)s,%(langue)s,%(langue_base)s,%(offset)s)",
                {
                    "keyword": keyword,
                    "engine": engine,
                    "langue": langue,
                    "langue_base": langue_base,
                    "offset": offset,
                },
            )
            res = cur.fetchall()

    return [res, count]


def get_page_db(livre, num_page):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM search_by_page(%(num_page)s,%(livre)s)""",
                {"livre": livre, "num_page": num_page},
            )
            return cur.fetchall()


def history(sens, langue):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT date_creation,traduction FROM data
                    WHERE sens=%(sens)s and id_langue=(select get_id_langue(%(langue)s))
                    ORDER BY date_creation desc;""",
                {"sens": sens, "langue": langue},
            )
            return cur.fetchall()


def list_langue(livre="all"):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            if livre == "all":
                cur.execute("SELECT nom_langue FROM langue;")
            else:
                cur.execute(
                    """SELECT nom_langue FROM langue
                    WHERE id_langue IN (SELECT id_langue
                                    FROM langue_dans_un_livre
                                    WHERE id_livre = (SELECT get_id_livre(%(livre)s)))
                            """,
                    {"livre": livre},
                )
            tempory = cur.fetchall()
            res = []
            for langue in tempory:
                res.append(langue[0])
            return res


def nb_page(livre):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT nom_langue FROM langue
                WHERE id_langue IN (SELECT id_langue
                                FROM langue_dans_un_livre
                                WHERE id_livre = (SELECT get_id_livre(%(livre)s)))
                        """,
                {"livre": livre},
            )
            tempory = cur.fetchall()
            print(tempory)
            res = []
            for langue in tempory:
                res.append(langue[0])
            return res


def insert_from_csv(
    filename, liste_langue, add_line_func
):  # pylint: disable=missing-function-docstring
    filename_csv = "release/" + filename + ".csv"
    reset_table()

    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO livre (nom_livre) VALUES (%(filename)s)",
                {"filename": filename},
            )
            for langue in liste_langue:
                add_langue(cur, langue, filename)
            with open(filename_csv, "r", encoding="utf-8") as file:
                liste_line = file.readlines()
                with tqdm(total=len(liste_line)) as pbar:
                    count = 0
                    for line in liste_line:
                        add_line_func(cur, line, filename, liste_langue, count)
                        count += 1
                        pbar.update()


if __name__ == "__main__":
    insert_from_csv(
        "hienghene-Fr",
        [
            "français",
            "pije",
            "fwâi",
            "nemi 1 (Temala)",
            "nemi 2 (côte est)",
            "jawe",
        ],
        hienghene_process,
    )
