from lib.system.utils import MultiProcessingTasks


def squares(i):
    return i*i


def cubes(i):
    return i*i*i


mp_task_obj = MultiProcessingTasks()

for i in range(1, 10):
    mp_task_obj.add_task(func=squares, func_args=(i,), task_key=i)
    mp_task_obj.add_task(func=cubes, func_args=(i,), task_key=i)

mp_task_obj.run()

for i in range(1, 10):
    print mp_task_obj.get_result(task_key=i)

