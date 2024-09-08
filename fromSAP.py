import pandas as pd
import re
import xlsxwriter
from datetime import datetime


def get_filenames():
    """
    получаю названия файла с итоговой выгрузкой из систем для гуи..
    :return:
    """
    cerf = 'deleteDismissed'
    return cerf


# noinspection PyTypeChecker
def get_data_from_lists(p, names):
    data = [pd.read_excel(open(p, 'rb'), sheet_name=names, usecols='A:B')]
    data2 = []
    for key in data[0]:
        data2.append(data[0][key])

    return data2


def update_fio(fio_series):
    """
    Разбиение ФИО на столбцы
    :param fio_series:
    :return: s1
    """
    s1 = pd.Series
    for i in range(len(fio_series)):
        try:
            fio_series[i] = re.sub(" +|\t", " ", fio_series[i])
            s1 = pd.Series(fio_series).str.split(' ', expand=True)
        except TypeError or IndexError:
            fio_series = ''
        finally:
            fio_series[i] = re.sub(" +|\t", " ", fio_series[i])
            s1 = pd.Series(fio_series).str.split(' ', expand=True)
    return s1


def update_data(dat_for_upd):
    dat_for_upd['Полное имя'] = dat_for_upd['Полное имя'].fillna(" ")
    fio_ser = update_fio(dat_for_upd['Полное имя'])

    if 'Пользователь' in dat_for_upd.columns.values.tolist():
        df3_merged = pd.concat([dat_for_upd['Пользователь'], fio_ser], axis=1)
        df3_merged.rename(columns={'Пользователь': 'УЗ', 0: 'Имя', 1: 'Отчество', 2: 'Фамилия'},
                          inplace=True)
    elif 'Имя пользов.' in dat_for_upd.columns.values.tolist():
        df3_merged = pd.concat([dat_for_upd['Имя пользов.'], fio_ser], axis=1)
        df3_merged.rename(columns={'Имя пользов.': 'УЗ', 0: 'Имя', 1: 'Отчество', 2: 'Фамилия'},
                          inplace=True)
    elif 'ИмяПользоват' in dat_for_upd.columns.values.tolist():
        df3_merged = pd.concat([dat_for_upd['ИмяПользоват'], fio_ser], axis=1)
        df3_merged.rename(columns={'ИмяПользоват': 'УЗ', 0: 'Имя', 1: 'Отчество', 2: 'Фамилия'},
                          inplace=True)

    df3_merged.dropna()
    df3_merged = df3_merged.drop([3, 4, 5, 6, 7, 8], axis=1, errors='ignore')
    df3_merged = df3_merged[['УЗ', 'Фамилия', 'Имя', 'Отчество']]

    return df3_merged


def create_prelast_xlsx(data_from_files, names):
    """
    создается финальный файл для работы с уз и фио
    :return:
    """
    workbook = xlsxwriter.Workbook('finalKEK.xlsx')
    worksheet = workbook.add_worksheet()
    workbook.close()

    for i, k in zip(data_from_files, names):
        with pd.ExcelWriter('finalKEK.xlsx', engine="openpyxl", mode='a') as writer:
            print(k)
            temp = update_data(i)
            temp.to_excel(writer, sheet_name=k)


# noinspection PyTypeChecker
def find_file():
    # todo найти или указать файл со внешними или внутренними
    file_path = 'выгрузка внутренние.xlsx'
    data_xlsx = [pd.read_excel(open(str(file_path), 'rb'), sheet_name='Лист1', usecols='A:D')]
    return data_xlsx


def del_na(dd):
    dd[0] = dd[0].fillna(" ")
    return dd


def upd_uz(uz):
    new_uz = []
    new_uz_simv = []
    # убрать длину строки 12 символов
    for i in range(len(uz['УЗ'])):
        new_uz.append(re.sub("cherkizovsky___|cherkizovsky|tk-cherkizovsky|bmpk|pmpk|ulyanovsky", "",
                             uz['УЗ'][i]).upper())
        new_uz_simv.append(new_uz[i][:12])

    return new_uz_simv


def upd_columns(dat_for_upd):
    clean = dat_for_upd[0]
    clean = clean[['УЗ', 'Фамилия', 'Имя', 'Отчество']]
    clean[['УЗ']] = pd.DataFrame(upd_uz(clean[['УЗ']]))

    return clean


def form_final_doc(final_data):
    with pd.ExcelWriter('from_postgreSQLvnutr.xlsx', mode='w') as writer:
        final_data.to_excel(writer)


# ______________________________________________________________________________________________________________________
# noinspection PyTypeChecker
def get_sys_data():
    data = [pd.read_excel(open('from_postgreSQLvnutr.xlsx', 'rb'), sheet_name='Sheet1', usecols='B:E')]
    return data


# noinspection PyTypeChecker
def get_postgre_data(file_names):
    data = [pd.read_excel(open('finalKEK.xlsx', 'rb'), sheet_name=file_names, usecols='B:E')]
    return data


def merging(sys, pos, file_names):
    workbook = xlsxwriter.Workbook('merged.xlsx')
    worksheet = workbook.add_worksheet()
    workbook.close()

    for i in file_names:
        with pd.ExcelWriter('merged.xlsx', engine="openpyxl", mode='a') as writer:
            temp = pd.merge(left=sys[0], right=pos[0][i], how='inner')
            if 0 == temp.shape[0]:
                pass
            else:
                temp.to_excel(writer, sheet_name=i)


if __name__ == "__main__":
    start_time = datetime.now()
    path = get_filenames()
    st_names = pd.ExcelFile(path).sheet_names
    all_lists_data = get_data_from_lists(path, st_names)
    create_prelast_xlsx(all_lists_data, st_names)
    print('формирование из систем ' + str(datetime.now() - start_time))
    start_time = datetime.now()
    data_fr_file = find_file()
    data_bez_na = del_na(data_fr_file)
    clean_data = upd_columns(data_bez_na)
    form_final_doc(clean_data)
    print('формирование из бд ' + str(datetime.now() - start_time))
    start_time = datetime.now()
    sys_data = get_sys_data()
    postgre = get_postgre_data(st_names)
    merging(sys_data, postgre, st_names)
    print('формирование итогового документа ' + str(datetime.now() - start_time))