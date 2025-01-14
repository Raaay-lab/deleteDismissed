import pandas as pd
import os
import re
import xlsxwriter
from datetime import datetime


def get_filenames():
    """
    получаю названия файлов из папки с расширение .xlsx
    :return:
    """
    file_ext = r".XLSX"
    list_for_upd = [_ for _ in os.listdir() if _.endswith(file_ext)]
    list_for_upd = [x.lower() for x in list_for_upd]
    return list_for_upd


# noinspection PyTypeChecker
def get_data_sheet1_all(list_filename):
    """
    получаю данные с sheet1
    :param list_filename:
    :return:
    """
    data_xlsx = []
    for i in list_filename:
        data_xlsx.append(pd.read_excel(open(i, 'rb'), sheet_name='Sheet1', usecols='A:B'))
    return data_xlsx


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


def create_prelast_xlsx(data_from_files, file_names):
    """
    создается финальный файл для работы с уз и фио
    :return:
    """
    with pd.ExcelWriter('finalKEK.xlsx', mode='w') as writer:
        temp = update_data(data_from_files[0])
        temp.to_excel(writer, sheet_name=file_names[0])

    del data_from_files[0]
    ff = file_names.copy()
    del ff[0]

    for i, k in zip(data_from_files, ff):
        with pd.ExcelWriter('finalKEK.xlsx', engine="openpyxl", mode='a') as writer:
            print(k)
            temp = update_data(i)
            temp.to_excel(writer, sheet_name=k)


# ______________________________________________________________________________________________________________________
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
    clean_data = dat_for_upd[0]
    clean_data = clean_data[['УЗ', 'Фамилия', 'Имя', 'Отчество']]
    clean_data[['УЗ']] = pd.DataFrame(upd_uz(clean_data[['УЗ']]))

    return clean_data


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

    merged_data = []
    for i in file_names:
        with pd.ExcelWriter('merged.xlsx', engine="openpyxl", mode='a') as writer:
            temp = pd.merge(left=sys[0], right=pos[0][i], how='inner')
            if 0 == temp.shape[0]:
                pass
            else:
                temp.to_excel(writer, sheet_name=i)


# def starting(sys_files, internal, external):
#     print(sys_files, internal, external)

def starting():
    start_time = datetime.now()
    file_names = get_filenames()
    data_from_files = get_data_sheet1_all(file_names)
    create_prelast_xlsx(data_from_files, file_names)
    print('формирование из систем ' + str(datetime.now() - start_time))
    start_time = datetime.now()
    data_fr_file = find_file()
    data_bez_na = del_na(data_fr_file)
    clean_data = upd_columns(data_bez_na)
    form_final_doc(clean_data)
    print('формирование из бд ' + str(datetime.now() - start_time))
    start_time = datetime.now()
    sys_data = get_sys_data()
    postgre = get_postgre_data(file_names)
    merging(sys_data, postgre, file_names)
    print('формирование итогового документа ' + str(datetime.now() - start_time))


if __name__ == "__main__":
    starting()
