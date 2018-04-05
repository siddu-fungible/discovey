#ifndef STCCAPI_H
#define STCCAPI_H

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__) || defined(WIN32)
# define STCCAPI_EXPORT  extern __declspec(dllexport) 
#else
# define STCCAPI_EXPORT  extern 
#endif


struct stccapi_str_vector {
    void* id;
};

typedef struct stccapi_str_vector stccapi_str_vector_t;

STCCAPI_EXPORT stccapi_str_vector_t* stccapi_str_vector_create(void);
STCCAPI_EXPORT int                   stccapi_str_vector_delete(stccapi_str_vector_t* vec);
STCCAPI_EXPORT int                   stccapi_str_vector_get_size(stccapi_str_vector_t* vec);
STCCAPI_EXPORT int                   stccapi_str_vector_append(stccapi_str_vector_t* vec, const char* item);
STCCAPI_EXPORT const char*           stccapi_str_vector_get_item(stccapi_str_vector_t* vec, int index);

STCCAPI_EXPORT const char* stccapi_get_last_err_msg();
STCCAPI_EXPORT int         stccapi_free_string(const char* str);

STCCAPI_EXPORT int         stccapi_init(void);
STCCAPI_EXPORT int         stccapi_shutdown(void);
STCCAPI_EXPORT int         stccapi_shutdown_with_exit_code(int exit_code);
STCCAPI_EXPORT int         stccapi_shutdown_no_exit(void);

STCCAPI_EXPORT const char* stccapi_create(const char* type, stccapi_str_vector_t* prop_pairs);
STCCAPI_EXPORT int         stccapi_delete(const char* handle);
STCCAPI_EXPORT int         stccapi_config(const char* handle, stccapi_str_vector_t* prop_pairs);
STCCAPI_EXPORT stccapi_str_vector_t* stccapi_get(const char* handle, stccapi_str_vector_t* prop_names);
STCCAPI_EXPORT stccapi_str_vector_t* stccapi_perform(const char* command_name, stccapi_str_vector_t* prop_pairs);
STCCAPI_EXPORT int         stccapi_log(const char* log_level, const char* msg);
STCCAPI_EXPORT const char* stccapi_help(const char* info);
STCCAPI_EXPORT int         stccapi_apply(void);
STCCAPI_EXPORT const char* stccapi_wait_until_complete(stccapi_str_vector_t* prop_pairs);

STCCAPI_EXPORT int         stccapi_connect(stccapi_str_vector_t* hosts);
STCCAPI_EXPORT int         stccapi_disconnect(stccapi_str_vector_t* hosts);
STCCAPI_EXPORT stccapi_str_vector_t* stccapi_reserve(stccapi_str_vector_t* csps);
STCCAPI_EXPORT int         stccapi_release(stccapi_str_vector_t* csps);
STCCAPI_EXPORT const char* stccapi_subscribe(stccapi_str_vector_t* prop_pairs);
STCCAPI_EXPORT int         stccapi_unsubscribe(const char* handle);

#ifdef __cplusplus
}
#endif 

#endif

