from StcIntPythonPL import *
import spirent.methodology.results.ProviderDataGenerator as pdg
from spirent.methodology.results.ResultEnum import EnumDataFormat, \
    EnumExecStatus, EnumVerdict, EnumDataClass
from spirent.methodology.results.ProviderConst import ProviderConst, ChartConst
import spirent.methodology.results.ProviderUtils as pu
import spirent.methodology.results.SqliteUtils as sql_utils


# base_template is customized by the author based on what
# type of chart is needed for specific methodology's report
base_template = {
    "title": {
        "text": "Y.1564 KPI Results",
        "x": -20
    },
    "xAxis": {
        "categories": "xcat",
        "labels": {
            "rotation": -45
        },
        "title": {
            "text": "Service/Frame Size"
        }
    },
    "yAxis": [{  # yAxis-1
        "categories": None,
        "title": {
            "text": "Latency (ms)",
            "style": {
                "color": '#434348'
            }
        },
        "opposite": True
    }, {  # yAxis-2
        "categories": None,
        "title": {
            "text": "Jitter (ms)",
            "style": {
                "color": '#7cb5ec'
            }
        }
    }, {  # yAxis-3
        "categories": None,
        "title": {
            "text": "Packet Count",
            "style": {
                "color": '#90ed7d'
            }
        },
        "opposite": True
    }],
    "tooltip": {
        "valueSuffix": " (ms)"
    },
    "series": [
        {
            "type": "column",
            "yAxis": 1,
            "name": "Min Jitter",
            "data": "min_jitter_data"
        },
        {
            "type": "column",
            "yAxis": 1,
            "name": "RFC4689 Avg Jitter",
            "data": "avg_jitter_data"
        },
        {
            "type": "column",
            "yAxis": 1,
            "name": "Max Jitter",
            "data": "max_jitter_data"
        },
        {
            "type": "column",
            "name": "Min Latency",
            "data": "min_latency_data"
        },
        {
            "type": "column",
            "name": "Avg Latency",
            "data": "avg_latency_data"
        },
        {
            "type": "column",
            "name": "Max latency",
            "data": "max_latency_data"
        },
        {
            "type": "column",
            "yAxis": 2,
            "name": "Packet Loss Count",
            "data": "pkt_loss_data"
        },
        {
            "type": "column",
            "yAxis": 2,
            "name": "Out of Order Packet Count",
            "data": "oop_data"
        },
        {
            "type": "column",
            "yAxis": 2,
            "name": "Late Packet Count",
            "data": "late_pkt_data_data"
        }
    ]
}


def CreateChart(tagname, b, params):
    plLogger = PLLogger.GetLogger('Methodology')
    plLogger.LogDebug("Running custom CreateChart script...")
    db_list = get_dbs(True, False)

    q_minjitter = str("SELECT ROUND(MinJitter*1e-3,3) FROM RxEotStreamResults As RxStr " +
                      "JOIN StreamBlock AS Sb " +
                      "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_avgjitter = str("SELECT ROUND(AvgJitter*1e-3,3) FROM RxEotStreamResults As RxStr " +
                      "JOIN StreamBlock AS Sb " +
                      "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_maxjitter = str("SELECT ROUND(MaxJitter*1e-3,3) FROM RxEotStreamResults As RxStr " +
                      "JOIN StreamBlock AS Sb " +
                      "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_minlatency = str("SELECT ROUND(MinLatency*1e-3,3) FROM RxEotStreamResults As RxStr " +
                       "JOIN StreamBlock AS Sb " +
                       "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_avglatency = str("SELECT ROUND(AvgLatency*1e-3,3) FROM RxEotStreamResults As RxStr " +
                       "JOIN StreamBlock AS Sb " +
                       "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_maxlatency = str("SELECT ROUND(MaxLatency*1e-3,3) FROM RxEotStreamResults As RxStr " +
                       "JOIN StreamBlock AS Sb " +
                       "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_pktloss = str("SELECT TxRes.FrameCount - RxRes.FrameCount " +
                    "As 'Packet Loss' From RxEotStreamResults As RxRes " +
                    "JOIN TxEotStreamResults As TxRes " +
                    "JOIN Streamblock As Sb " +
                    "ON RxRes.ParentStreamBlock = TxRes.ParentStreamblock " +
                    "AND TxRes.ParentStreamblock = Sb.Handle")
    q_ooopkt = str("SELECT OutSeqFrameCount FROM RxEotStreamResults As RxStr " +
                   "JOIN StreamBlock AS Sb " +
                   "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_latepkt = str("SELECT LateFrameCount FROM RxEotStreamResults As RxStr " +
                    "JOIN StreamBlock AS Sb " +
                    "ON RxStr.ParentStreamBlock == Sb.Handle")
    q_xcat = str("SELECT Name || '/' || Sb.FixedFrameLength " +
                 "FROM RxEotStreamResults As RxStr " +
                 "JOIN StreamBlock AS Sb " +
                 "ON RxStr.ParentStreamBlock == Sb.Handle")

    min_jitter_data = get_data_from_query(db_list, q_minjitter)
    avg_jitter_data = get_data_from_query(db_list, q_avgjitter)
    max_jitter_data = get_data_from_query(db_list, q_maxjitter)
    min_latency_data = get_data_from_query(db_list, q_minlatency)
    avg_latency_data = get_data_from_query(db_list, q_avglatency)
    max_latency_data = get_data_from_query(db_list, q_maxlatency)
    pktloss_data = get_data_from_query(db_list, q_pktloss)
    ooopkt_data = get_data_from_query(db_list, q_ooopkt)
    latepkt_data = get_data_from_query(db_list, q_latepkt)
    xcat_data = get_data_from_query(db_list, q_xcat)

    base_template['series'][0]['data'] = min_jitter_data
    base_template['series'][1]['data'] = avg_jitter_data
    base_template['series'][2]['data'] = max_jitter_data
    base_template['series'][3]['data'] = min_latency_data
    base_template['series'][4]['data'] = avg_latency_data
    base_template['series'][5]['data'] = max_latency_data
    base_template['series'][6]['data'] = pktloss_data
    base_template['series'][7]['data'] = ooopkt_data
    base_template['series'][8]['data'] = latepkt_data
    base_template['xAxis']['categories'] = xcat_data

    result_data = init_chart_data_dict("GROUP_1")

    pdg.submit_provider_data(result_data)

    return ""


def get_data_from_query(db_file_list, query):
    result_data = sql_utils.get_all_data(db_file_list, query)
    rows = result_data[ProviderConst.ROW]
    row_data = []
    for row in rows:
        row_data.append(row[0])
    return row_data


def get_dbs(UseMultipleResultsDatabases, UseSummary):
    if UseSummary and not UseMultipleResultsDatabases:
        return [get_active_results_db()]
    return pu.get_db_files(get_active_results_db(), UseMultipleResultsDatabases)


def get_active_results_db():
    # In its own function to allow for easier unit testing using MagicMock
    return pu.get_active_result_db_filename()


def init_chart_data_dict(ReportGroup):
    info = {
        ProviderConst.REPORT_GROUP: ReportGroup
    }
    status = {
        ProviderConst.VERDICT: EnumVerdict.none,
        ProviderConst.VERDICT_TEXT: '',
        ProviderConst.EXEC_STATUS: EnumExecStatus.completed,
        ProviderConst.APPLY_VERDICT: 'false'
    }
    data = {
        ChartConst.BASE_NAME: base_template,
        # ChartConst.TITLE: base_template['title'],
        # ChartConst.X_CAT: base_template['xAxis']['categories'],
        # ChartConst.X_LAB: base_template['xAxis']['title'],
        # ChartConst.Y_CAT: '',
        # ChartConst.Y_LAB: base_template['yAxis']['title'],
        # ChartConst.SERIES: '',
        # ChartConst.MOD_LIST: ''
        ChartConst.TITLE: '',
        ChartConst.X_CAT: '',
        ChartConst.X_LAB: '',
        ChartConst.Y_CAT: '',
        ChartConst.Y_LAB: '',
        ChartConst.SERIES: '',
        ChartConst.MOD_LIST: ''
    }
    provider_data = {
        ProviderConst.DATA_FORMAT: EnumDataFormat.chart,
        ProviderConst.CLASS: EnumDataClass.methodology_chart,
        ProviderConst.INFO: info,
        ProviderConst.STATUS: status,
        ProviderConst.DATA: data
    }
    return provider_data
