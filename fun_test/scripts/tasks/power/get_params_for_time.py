from lib.system.fun_test import *


def get(time, crypto_per=100, zip_per=100, rcnvme_per=70, fio_per=100):
    result = False
    app_params = {}
    try:
        if time == 60:
            rcnvme_run_time = 100
            fio_run_time = 100
            zip_factor = 1
            crypto_factor = 1
        elif time == 3600:
            rcnvme_run_time = 3600
            fio_run_time = 3600
            zip_factor = 5
            crypto_factor = 20
        elif time == 14400:
            rcnvme_run_time = 14400
            fio_run_time = 14400
            zip_factor = 20
            crypto_factor = 50
        standard = {
            "crypto": {
                "10": {"vp_iters": 15000000 * crypto_factor, "nvps": 3},
                "20": {"vp_iters": 15000000 * crypto_factor, "nvps": 13},
                "30": {"vp_iters": 15000000 * crypto_factor, "nvps": 17},
                "40": {"vp_iters": 15000000 * crypto_factor, "nvps": 22},
                "50": {"vp_iters": 15000000 * crypto_factor, "nvps": 25},
                "60": {"vp_iters": 15000000 * crypto_factor, "nvps": 32},
                "70": {"vp_iters": 15000000 * crypto_factor, "nvps": 45},
                "80": {"vp_iters": 10000000 * crypto_factor, "nvps": 55},
                "90": {"vp_iters": 10000000 * crypto_factor, "nvps": 70},
                "100": {"vp_iters": 5000000 * crypto_factor, "nvps": 192}
            },
            "zip": {
                "10": {"nflows": 6, "niterations": 40000 * zip_factor},
                "20": {"nflows": 30, "niterations": 40000 * zip_factor},
                "30": {"nflows": 60, "niterations": 40000 * zip_factor},
                "40": {"nflows": 70, "niterations": 40000 * zip_factor},
                "50": {"nflows": 90, "niterations": 40000 * zip_factor},
                "60": {"nflows": 105, "niterations": 40000 * zip_factor},
                "70": {"nflows": 120, "niterations": 40000 * zip_factor},
                "80": {"nflows": 130, "niterations": 40000 * zip_factor},
                "90": {"nflows": 140, "niterations": 40000 * zip_factor},
                "100": {"nflows": 7680, "niterations": 500 * zip_factor}
            },
            "rcnvme": {
                "10": {"qdepth": 4, "nthreads": 1, "duration": rcnvme_run_time},
                "20": {"qdepth": 6, "nthreads": 1, "duration": rcnvme_run_time},
                "30": {"qdepth": 4, "nthreads": 2, "duration": rcnvme_run_time},
                "40": {"qdepth": 6, "nthreads": 2, "duration": rcnvme_run_time},
                "50": {"qdepth": 8, "nthreads": 2, "duration": rcnvme_run_time},
                "60": {"qdepth": 8, "nthreads": 4, "duration": rcnvme_run_time},
                "70": {"qdepth": 12, "nthreads": 12, "duration": rcnvme_run_time},
            },
            "fio": {
                "10": {"num_jobs": 8, "iodepth": 1, "run_time": fio_run_time},
                "35": {"num_jobs": 8, "iodepth": 4, "run_time": fio_run_time},
                "65": {"num_jobs": 8, "iodepth": 8, "run_time": fio_run_time},
                "100": {"num_jobs": 8, "iodepth": 16, "run_time": fio_run_time}
            }
        }
        result = {}

        for key in standard:
            app_params[key] = standard[key][str(eval(key+"_per"))]
        result = True
    except Exception as ex:
        fun_test.critical(ex)
    fun_test.test_assert(result, "Got the app parameters for time : {} min".format(time))
    return app_params


# unit : minutes


if __name__ == "__main__":
    print get(1)
