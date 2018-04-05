from StcIntPythonPL import *
import sqlite3
import spirent.methodology.utils.sql_utils as sql_utils
import spirent.methodology.utils.tag_utils as tag_utils


def tag_bgp_globals():
    stc_sys = CStcSystem.Instance()
    proj = stc_sys.GetObject("Project")
    bgp_globals = proj.GetObject("BgpGlobalConfig")
    tag_utils.add_tag_to_object(bgp_globals, "tBgpGlobalConfig")


def run(notused_tagname, notused_tagged_targets, notused_param_string):

    # First let's tag the BgoGlobalConfig for use later...
    tag_bgp_globals()

    # Protect us from an SQL error...
    try:
        err, db_list = sql_utils.get_dbs_list("SUMMARY")
        if len(db_list) == 0:
            return 'Summary db not available...'
        err, con, cursor = sql_utils.connect_db(db_list[0])
        if err:
            return err

        # Get the min/max/step values that will be used...
        cursor.execute("SELECT \"First Flow Spec Count\", \"Last Flow Spec Count\"," +
                       "\"Flow Spec Count Step\" FROM MethIterconfig")
        iter = cursor.fetchone()
        first = iter[0]
        last = iter[1]
        step = iter[2]

        # We cannot utilize a negative step value...
        if step < 0:
            return "The flow spec count step value must not be negative."

        # If step is zero, then error if first and last are not equal...
        if first != last and step < 1:
            return "The flow spec range is not zero, so the step must not be less than one."

        # If the range is negative but with a positive step, then error...
        if first > last:
            return "The flow spec range is backward: " + str(first) + " to " + str(last)

        # Get the distribution schedule...
        cursor.execute("SELECT * FROM MethBgpFlowSpecConfig")
        schedule = cursor.fetchone()

        # Ensure that the distribution totals 100%...
        if sum(schedule) != 100:
            return "The distribution schedule for the flow spec types " + \
                "does not equal 100 (%): " + str(schedule)

        iter_config = calc_distribution(schedule, first, last, step)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS MethIterConfigurations (
                'Type-1 Enable',
                'Type-1 Start',
                'Type-1 Count',
                'Type-2 Enable',
                'Type-2 Start',
                'Type-2 Count',
                'Type-4 Enable',
                'Type-4 Start',
                'Type-4 Count',
                'Type-5 Enable',
                'Type-5 Start',
                'Type-5 Count',
                'Type-6 Enable',
                'Type-6 Start',
                'Type-6 Count',
                'Type-10 Enable',
                'Type-10 Start',
                'Type-10 Count'
                )
                ''')
        cursor.executemany("INSERT INTO MethIterConfigurations VALUES" +
                           "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", iter_config)
        con.commit()
        con.close()
    except sqlite3.Error as e:
        return "A SQL error occurred: " + e.args[0]
    return ''


def calc_distribution(schedule, first, last, step):
    plLogger = PLLogger.GetLogger('methodology')
    # FIXME: We need to add back in Type-11...
    next_start_value = [1, 1, 1, 1, 1, 1]
    iter_config = []
    currval = first
    working = first
    i = 0
    while currval <= last:
        iter_row = []
        distribution = [int(working * s / 100) for s in schedule]
        plLogger.LogInfo('Initial distribution of working count ' + str(working) +
                         ' across flow spec schedule: ' + str(distribution))
        remainder = working - sum(distribution)
        while remainder > 0:
            if schedule[i] > 0:
                distribution[i] += 1
                remainder -= 1
            i = (i + 1) if i + 1 < len(distribution) else 0

        # From each distribution count, we need to create an enable flag,
        # a start value for that type for that iteration, and the count
        # of that type for that iteration.
        for index, count in enumerate(distribution):
            iter_row.append(0 if count == 0 else 1)
            next_start_value[index], v = start_value(index, next_start_value[index], count)
            iter_row.append(v)
            iter_row.append(count)

        iter_config.append(iter_row)
        currval += step
        working = step
        # If the user said they want a step of 0, then we plan for only one iteration...
        if step == 0:
            break

    return iter_config


def start_value(index, start, count):
    if index < 2:
        return start + (0 if count == 0 else 1), str(int(start)) + ".0.0.0"
    return start + count, start
