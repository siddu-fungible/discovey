from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import DATA_STORE_DIR
import time
import re
import os
import json


class RegexTemplate(Linux):
        mem_dict = {
            "dflt": "Default Memory Allocation ",
            "rbm": "RBM Only Graph",
            "exm": "EXM Only Graph",
            "exm_plr": "EXM Only Graph, Root preloaded",
            "rbm_exm": "Some NFA portion in RBM ",
            "rbm_exm_plr": "Some NFA portion in RBM, Root Preloaded"
        }

        strategy_dict = {
            "0": "NFA",
            "1": "DFA"
        }

        @fun_test.safe
        def set_compiler_env(self, compiler_path):
            self.command('export PATH="{}:$PATH"'.format(compiler_path))

        @fun_test.safe
        def get_file_size(self, file_name):
            op = self.command('ls -lh {}'.format(file_name))
            if "No such file" in op:
                fs = None
            else:
                fs = op.split(" ")[8]
            return fs

        @fun_test.safe
        def get_ffac_version(self):
            op = self.command('ffac | grep tag')
            version = re.search("bld_\d+", op).group()
            return version

        @fun_test.safe
        def compile_re(self, time_out=120, **compiler_args):
            args = compiler_args.items()
            payload_buffs =[0,0]
            results = []
            cmd = 'ffac '
            graph_path = ""
            print "args: ", args
            for arg in args:
                #if "pat_dump_file" in arg:
                if "drop_unsupported" in arg:
                    cmd = cmd + "--" + arg[0] + " " + arg[1] + " "
                elif "no_exm" in arg:
                    cmd = cmd + "--" + arg[0] + " " + arg[1] + " "
                elif "o" in arg:
                    graph_path = arg[1]
                    cmd = cmd + "-" + arg[0] + " " + arg[1] + " "
                elif "j" in arg:
                    if arg[1] == "yes":
                        cmd = cmd + "-" + arg[0] + " "
                else:
                    cmd = cmd + "-" + arg[0] + " " + arg[1] + " "
            self.logger.log("\n\n=======================COMMAND BEING USED: "+cmd+"\n\n")
            compilation_time = None
            try:
                time_start = time.time()
                op = self.command(cmd, timeout=time_out)
                time_end = time.time()
                compilation_time = "{0:.2f}".format((time_end - time_start))
                '''
                if not "p" in compiler_args.keys():
                    if "ERROR" in op:
                        self.logger.log("ERROR in ffac output: "+op+"\n")
                        return False, op, compilation_time
                    if "CRITICAL" in op:
                        self.logger.log("CRITICAL in ffac output: "+op+"\n")
                        return False, op, compilation_time
                    if ("Segmentation fault" in op) or ("Assertion failed"  in op):
                        self.logger.log("Segmentation fault in ffac output: "+op+"\n")
                        return False, op, compilation_time
                    if ("Aborted" in op) or ("core dump"  in op):
                        self.logger.log("Aborted or core dumped. ffac output: "+op+"\n")
                        return False, op, compilation_time
                    else:
                        cmd = "ls -l " + graph_path
                        print "cmd:", cmd
                        output = self.command(cmd, timeout=time_out)
                        print "output of ls -1", output
                        cmd = "ls -la " + graph_path + " | awk '{print $5}'"
                        graph_size = self.command(cmd, timeout=time_out)
                        print "returning graph size:", graph_size
                        return True, op, compilation_time, graph_size
                '''
                if "ERROR" in op:
                    self.logger.log("ERROR in ffac output: " + op + "\n")
                    return False, op, compilation_time
                if "CRITICAL" in op:
                    self.logger.log("CRITICAL in ffac output: " + op + "\n")
                    return False, op, compilation_time
                if ("Segmentation fault" in op) or ("Assertion failed" in op):
                    self.logger.log("Segmentation fault in ffac output: " + op + "\n")
                    return False, op, compilation_time
                if ("Aborted" in op) or ("core dump" in op):
                    self.logger.log("Aborted or core dumped. ffac output: " + op + "\n")
                    return False, op, compilation_time
                else:
                    cmd = "ls -l " + graph_path
                    print "cmd:", cmd
                    output = self.command(cmd, timeout=time_out)
                    print "output of ls -1", output
                    cmd = "ls -la " + graph_path + " | awk '{print $5}'"
                    graph_size = self.command(cmd, timeout=time_out)
                    print "returning graph size:", graph_size
                    return True, op, compilation_time, graph_size
            except:
                self.logger.log("compilation problem: "+op+"\n")
                return False, results, compilation_time
            '''
            if "ERROR" in op:
                self.logger.log("ERROR in ffac output: "+op+"\n")
                return False, op, compilation_time
            if "CRITICAL" in op:
                self.logger.log("CRITICAL in ffac output: "+op+"\n")
                return False, op, compilation_time
            if "Segmentation fault" in op:
                self.logger.log("Segmentation fault in ffac output: " + op + "\n")
                return False, op, compilation_time
            '''
            if "p" in compiler_args.keys():
                match_list = None
                try:
                    op = op.split("HERE ARE THE FINAL ANSWERS")[-1]
                    match_list = re.findall("(?:Id:\s.*)", op)
                    if "NONE" in match_list[-1]:
                        del match_list[-1]
                except:
                    self.logger.log("Could not find Answers in output: "+op+"\n")
                    return False, op, compilation_time
                for num, match in enumerate(match_list):
                    try:
                       pat_name = re.search("pat_name: (\w+)", match).group(1)
                       pat_id = re.search("Id: (\w+|\d+)", match).group(1)
                       Id = int(pat_id)
                       s_off = re.search("start: (\w+)", match).group(1)
                       if s_off == "xx":
                           start_offset = -1
                       else:
                           start_offset = int(s_off)
                       #FIXME Including match offset -1 as of now
                       e_off = re.search("end: (\w+|\d+|-1)", match).group(1)
                       if e_off == "xx":
                           end_offset = -1
                       else:
                           end_offset = int(e_off)

                       #ml = [Id, payload_buffs[0], start_offset, payload_buffs[1], end_offset, pat_name]
                       ml = [pat_name, payload_buffs[0], start_offset, payload_buffs[1], end_offset]
                       results.append(ml)
                      
                    except:
                       print ("No matches found or Incorrect id")
                # Remove duplicates
                results = [list(tupl) for tupl in {tuple(item) for item in results}]
                return True, results, compilation_time 
            else:
                self.logger.log("compilation issue: "+op+"\n")
                return False, results, compilation_time

        @fun_test.safe
        def compile_n_validate(self, mem_dist, pat_path, pld_path, res_path, exclude_lst=[], engine="", juniper_style="",  time_out=60):
            pld_files_dict = self.list_files(pld_path)
            jstyle = "yes"
            pld_files = [fn['filename'] for fn in pld_files_dict]
            print "pld_files:", pld_files
            build = self.get_ffac_version()
            if engine == "":
                strategy = "FFA"
            else:
                strategy = RegexTemplate.strategy_dict[engine]

            if juniper_style == "":
                jstyle = "no"

            for idx, pld in enumerate(pld_files):
                try:
                    base = re.search("test_\d+", pld).group()
                except:
                    continue
                if base in exclude_lst:
                    print "Excluding ", base, ".......\n"
                    continue
                print "pld:", pld
                pld_base = re.search("test_\d+_\d+", pld).group()
                #for mem in ["dflt", "rbm", "exm", "exm_plr", "rbm_exm", "rbm_exm_plr"]:
                for mem in mem_dist:
                    graph_name = base + "_" + mem + "_graph.json"
                    try:
                        if engine == "1":
                            if mem == "dflt":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", L=" ", e=engine, r=pat_path + base + '.pat',
                                                    p=pld_path + pld, o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", L=" ", e=engine, r=pat_path + base + '.pat',
                                                    p=pld_path + pld, o=res_path + graph_name, time_out=time_out)
                        elif engine == "0":
                            if mem == "dflt":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", L=" ", e=engine, r=pat_path + base + '.pat',
                                                    p=pld_path + pld, o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine, r=pat_path + base + '.pat',
                                                    p=pld_path + pld, o=res_path + graph_name, time_out=time_out)
                        else:
                            if mem == "dflt":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", L=" ", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)
                            if mem == "rbm_exm_plr":
                                op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", L=" ", r=pat_path + base + '.pat', p=pld_path + pld,
                                                    o=res_path + graph_name, time_out=time_out)

                    except Exception as e:
                        op = (False, 'TIMEOUT', '0.0')
                        fun_test.log("Compilation failed")
                    actual_op = op[1]
                    fun_test.log(op)
                    time_size = ""
                    graph_sz = ""
                    compile_time = ""
                    if op[0] is True:
                        graph_sz = op[3]
                        compile_time = op[2]
                        time_size = " graph size:" + graph_sz + " compilation time:" + compile_time

                    result_str = "Compile: (" + strategy + " Strategy) " + RegexTemplate.mem_dict[
                        mem] + ": " + base + '.pat'  + "=> " + build + time_size
                    try:
                        if op[0] is False:
                            if 'TIMEOUT' in op[1]:
                                result_str += 'TIMEOUT'
                            else:
                                fail_op_lst = op[1].split("\n")
                                result_str += "".join(fail_op_lst[-5:])

                        fun_test.test_assert(op[0], result_str + "\n")
                    except:
                        pass

                    #res_file = DATA_STORE_DIR + res_path + pld_base + "_" + mem + ".json"
                    res_file = DATA_STORE_DIR + res_path + pld_base + ".json"

                    try:
                        json_file = open(res_file, "r")
                    except IOError:
                        try:
                            fun_test.test_assert(False, "Validate: Failed to open JSON file ! " + res_file)
                        except:
                            continue
                    try:
                        print "trying to read parsed_json"
                        parsed_json = json.loads(json_file.read())
                        print "parsed_json:", parsed_json
                        # exp_op = parsed_json[2]["RESULTS"]
                        exp_ans = parsed_json["parallel"][0][1]["payload"][0]["expected"]
                        exp_op = []
                        for ans in exp_ans:
                            ml = [ans["name"], ans["s_gidx"], ans["s_goff"], ans["e_gidx"], ans["e_goff"]]
                            exp_op.append(ml)
                    except:
                        exp_op = None
                        try:
                            fun_test.test_assert(False,
                                                 "Validate: Failed to read expected section from JSON file !  " + res_file)
                        except:
                            continue
                    if len(sorted(exp_op)) == len(sorted(actual_op)):
                        compare_lst = [i for i, j in zip(sorted(actual_op), sorted(exp_op)) if i != j]
                    else:
                        compare_lst = ["dummy"]
                    fun_test.log("Actual: ")
                    fun_test.log(sorted(actual_op))
                    fun_test.log("Expected: ")
                    fun_test.log(sorted(exp_op))
                    fun_test.log("Compare lst: ")
                    fun_test.log(compare_lst)
                    validate_str = ""
                    try:
                        if (len(compare_lst) != 0):
                            validate_str = "   \nActual: " + str(sorted(actual_op)) + "Expected: " + str(sorted(exp_op))
                        fun_test.test_assert(len(compare_lst) == 0,
                                             "Validate:" + mem + ":" + pld + "=> " + validate_str)
                    except:
                        pass

        @fun_test.safe
        def compile_only(self, mem_dist, pat_path, res_path, exclude_lst=[], engine="", juniper_style="", time_out=2 * 60):
            pat_files_dict = []
            base = ""
            jstyle = "yes"
            pat_files_dict = self.list_files(pat_path + "*")
            pat_files = [fn['filename'] for fn in pat_files_dict]
            build = self.get_ffac_version()
            print "BUILD:", build
            if engine == "":
                strategy = "FFA"
            else:
                strategy = RegexTemplate.strategy_dict[engine]

            if juniper_style == "":
                jstyle = "no"

            for idx, pat in enumerate(pat_files):
                print "pat:", pat
                prefix = os.path.basename(pat)
                pfx = os.path.splitext(prefix)[0]
                base = pfx
                if base:
                    ### for mem in ["dflt", "rbm", "exm", "exm_plr", "rbm_exm", "rbm_exm_plr"]:
                    #for mem in ["exm"]:
                    for mem in mem_dist:
                        graph_name = base + "_" + mem + "_graph.json"
                        ptrn = pat_path + prefix
                        try:
                            if engine == "0":
                                if mem == "dflt":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", B="0", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", B="0", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)

                            elif engine == "1":
                                if mem == "dflt":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=ptrn,
                                                       o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)

                            else:
                                if mem == "dflt":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", L=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", L=" ",
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out)

                        except Exception as e:
                            op = (False, 'TIMEOUT', '0.0')
                            fun_test.log("Compilation failed")
                        actual_op = op[1]
                        #fun_test.log("COMPILER OUTPUT:")
                        fun_test.log(op[1])
                        myslices = ""
                        dfa_slices = str(re.findall("Mapped DFA.*", op[1]))
                        nfa_slices = str(re.findall("Mapped NFA.*", op[1]))
                        print "DFA:", dfa_slices, " NFA:", nfa_slices
                        myslices = dfa_slices + nfa_slices
                        print "myslices:", myslices

                        time_size = ""
                        graph_sz = ""
                        compile_time = ""
                        if op[0] is True:
                            graph_sz = op[3]
                            compile_time = op[2]
                            time_size = " size:" + myslices + " compilation time:" + compile_time

                        result_str = "Compile: (" + strategy + " Strategy) " + RegexTemplate.mem_dict[
                            mem] + ": " + pat + "=> " + build + time_size


                        try:
                            if op[0] is False:
                                fail_count += 1
                                if 'TIMEOUT' in op[1]:
                                    result_str += 'TIMEOUT'
                                else:
                                    fail_op_lst = op[1].split("\n")
                                    result_str += "".join(fail_op_lst[-5:])
                            fun_test.test_assert(op[0], result_str + "\n")
                            print "we are here now, can return build ", build
                            #return build
                        except:
                            pass

        @fun_test.safe
        def validate_matches(self, actual_lst = [], expeted_lst =[]):
            pass

        @fun_test.safe
        def validate_pcre_matches(self):
            pass

        @fun_test.safe
        def create_regex_jsons(self):
            pass

        @fun_test.safe
        def gen_random_pats(self):
            pass

        @fun_test.safe
        def gen_payload(self):
            pass

        @fun_test.safe
        def extract_pld_data(self):
            pass

