from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import DATA_STORE_DIR
import time
import re
import os
import json
import collections
import random as r


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
        def create_exp_file(self,op,pld_len):
            # type: (object, object, object, object) -> object
            exp_matches=[]
            self.logger.log("first checkpoint")
            match_list = re.findall("(?:Id:\s.*)", op)
            self.logger.log("match_list is")
            self.logger.log(match_list)
            self.logger.log("second checkpoint")
            self.logger.log("checkpoint")
            #self.logger.log("match_list[-1]",match_list[-1])
            #if "NONE" in match_list[-1]:
            #    self.logger.log("no match results observed")
            #    del match_list[-1]
            self.logger.log("third checkpoint")
            if match_list != []:
                for match in match_list:
                    try:
                        pat_name = re.search("pat_name: (\w+)", match).group(1)
                        s_off= re.search("start: (\w+|\d+|-1)", match).group(1)
                        e_off = re.search("end: (\w+|\d+|-1)", match).group(1)
                        if s_off == "xx":
                            start_offset = -1
                        else:
                            start_offset = int(s_off)
                        # FIXME Including match offset -1 as of now
                        if e_off == "xx":
                            end_offset = -1
                        else:
                            end_offset = int(e_off)
                        s_gidx = e_gidx = 0
                        match_dict = {"name": pat_name, "s_gidx": s_gidx, "s_goff":start_offset,
                                      "e_gidx": e_gidx, "e_goff": end_offset}

                        exp_matches.append(match_dict)

                    except:
                        print ("something went wrong in creating expected output file")
                expected_dict={"expected": exp_matches}
                return expected_dict
            print ("new if condition")
            if match_list==[]:
                print("inside if condition")
               # self.logger.log("else statement inside create_exp_file")
                self.logger.log("exp_matches are")
                self.logger.log(exp_matches)
                expected_dict=dict(expected=exp_matches)
                self.logger.log("exp matches for empty results are ")
                self.logger.log(exp_matches)
                return expected_dict




        @fun_test.safe
        def compile_re(self, time_out=120, **compiler_args):
            print ("compiler args are ",compiler_args.items())
            args = compiler_args.items()
            payload_buffs =[0,0]
            results = []
            cmd = 'ffac '
            graph_path = ""
            #pat_prefix = (os.path.basename(compiler_args["p"])).split(".pat")[0]
            #pld_prefix=os.path.basename(compiler_args["r"])

            print "Entered compile_re: args: ", args
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
                elif "target" in arg:
                    if arg[1] == "s1":
                        cmd = cmd + "--" + arg[0] + "=" + arg[1] + " "
                    if arg[1] == "f1":
                       cmd = cmd + "--" + arg[0] + "=" + arg[1] + " "
                else:
                    self.logger.log("else statement")
                    cmd = cmd + "-" + arg[0] + " " + arg[1] + " "
            print ("graph path is ",graph_path)
            self.logger.log("\n\n=======================COMMAND BEING USED: "+cmd+"\n\n")
            print ("ffac command  used is ",cmd)
            compilation_time = None
            try:
                time_start = time.time()
                op = self.command(cmd, timeout=time_out)
                time_end = time.time()
                print("****************")
                print("compiler_args",compiler_args.keys())
                compilation_time = "{0:.2f}".format((time_end - time_start))
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
                if not 'p' in compiler_args.keys():
                        cmd = "ls -l " + graph_path
                        print "cmd:", cmd
                        output = self.command(cmd, timeout=time_out)
                        print "output of ls -1", output
                        cmd = "ls -la " + graph_path + " | awk '{print $5}'"
                        graph_size = self.command(cmd, timeout=time_out)
                        print "returning graph size:", graph_size
                        return True, op, compilation_time, graph_size

                if 'p' in compiler_args.keys():
                    match_list=[]
                    match_list = None
                    try:
                        cmd = "ls -l " + graph_path
                        print "cmd:", cmd
                        output = self.command(cmd, timeout=time_out)
                        print "output of ls -1", output
                        cmd = "ls -la " + graph_path + " | awk '{print $5}'"
                        graph_size = self.command(cmd, timeout=time_out)
                        print "returning graph size:", graph_size
                        op = op.split("HERE ARE THE FINAL ANSWERS")[-1]
                        print (op)
                        match_list = re.findall("(?:Id:\s.*)", op)
                        if "NONE" in match_list[-1]:
                            del match_list[-1]
                        if match_list!=[]:
                            return True,op,compilation_time,graph_size
                        else:
                            print ("match results not found")
                            return False,op,compilation_time,graph_size
                    except:
                        print ("caught an exception")
                        self.logger.log("Could not find Answers in output: " + op + "\n")
                        return True,"could not find answers", compilation_time,graph_size

            except:
                self.logger.log("compilation problem: "+op+"\n")
                return False, results, compilation_time


        @fun_test.safe
        def compile_n_validate(con1, mem_dist, pat_path, pld_path, res_path, exp_file_path, pat_pld_files, exclude_lst=[],
                               engine="",juniper_style="", target="",time_out= 5 * 60):

            """

            :type target: object
            """
            trgt="f1"
            compilation_failed=validation_failed=0
            print ("compile and validation function")
            print ("pat_pld_files are ",pat_pld_files)
            print ("pat_pld_fileS_items are ",pat_pld_files.items())
            jstyle = "yes"
            if target=="s1":
                trgt="s1"
            for pat,plds in pat_pld_files.items():
                print ("pattern is",pat)
                print ("payload is ",plds)
                build = con1.get_ffac_version()
                if engine == "":
                    strategy = "FFA"
                    print ("strategy is ",engine)
                else:
                    strategy = RegexTemplate.strategy_dict[engine]

                if juniper_style == "":
                    jstyle = "no"

                for idx,pld in enumerate(plds):
                    con1.logger.log("pld is : ")
                    con1.logger.log(pld)
                    try:
                        base = pat.split(".pat")[0]
                    except:
                        continue
                    if base in exclude_lst:
                        print "Excluding ", base, ".......\n"
                        continue
                    print "pld:", pld

                    if juniper_style=="yes_snort" and jstyle=="yes":
                        print ("testing snort cases")
                        jstyle=="yes"
                        pattern_path=pat_path+pat
                        payload_path=pld_path+pld

                    elif jstyle=="yes":
                        print ("juniper yes condition")
                        pattern_path=pat_path+base+"/"+pat
                        payload_path=pld_path+base+"/payloads/"+pld
                    else:
                        print ("else condition")
                        pattern_path=pat_path+pat
                        payload_path=pld_path+pld
                        print ("payload  path is",payload_path)
                        print("pattern path is ",pattern_path)

                    con1.logger.log("pattern path for compilation")
                    con1.logger.log(pattern_path)
                    con1.logger.log("payload_path for compilation is ")
                    con1.logger.log(payload_path)
#                    pld_base = re.search("test_\d+_\d+", pld).group()
                    #for mem in ["dflt", "rbm", "exm", "exm_plr", "rbm_exm", "rbm_exm_plr"]:
                    cmd="ls -la " + payload_path + " | awk '{print $5}'"
                    payload_len = con1.command(cmd,timeout=time_out)
                    print ("payload len is ",payload_len)
                    for mem in mem_dist:
                        con1.logger.log("memory is :")
                        con1.logger.log(mem)
                        graph_name = base + "_" + mem + "_graph.json"
                        print ("second_check_point")
                        try:
                            if engine == "1":
                                print ("DFA")
                                if mem == "dflt":
                                    op = con1.compile_re(j=jstyle,  drop_unsupported=" ", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, target=trgt, s="1500", time_out=time_out)
                                if mem == "rbm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "exm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", B="0", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt , time_out=time_out)
                                if mem == "exm_plr":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", B="0", L=" ", e=engine, r=pattern_path,
                                                        p=payload_path, o=res_path + graph_name, s="1500",target=trgt ,time_out=time_out)
                                if mem == "rbm_exm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", B="10", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", B="10", L=" ", e=engine, r=pattern_path,
                                                        p=payload_path, s="1500", o=res_path + graph_name, target=trgt, time_out=time_out)
                            elif engine == "0":
                                print ("NFA")
                                if mem == "dflt":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "rbm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "exm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", H="0", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "exm_plr":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", H="0", L=" ", e=engine, r=pat_path + base +"/"+pat,
                                                        p=pld_path+base+"/payloads/"+base+".in", target=trgt, o=res_path + graph_name, s="1500", time_out=time_out)
                                if mem == "rbm_exm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=pattern_path, p=payload_path,
                                                        o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine,r=pattern_path,
                                                        p=payload_path, o=res_path + graph_name, s="1500", target=trgt, time_out=time_out)
                            else:
                                print ("FFA")
                                if mem == "dflt":
                                    print ("FFA:defaukt")
                                    print ("inside dflt")
                                   # op = self.compile_re(j=jstyle, drop_unsupported=" ", r=pat_path+base+"/pattern/"+pat, p=pld_path+base+"/payloads/"+base+".in",
                                                        #o=res_path + graph_name, time_out=time_out)
                                    #op = self.compile_re(j=jstyle, drop_unsupported=" ",r=pat_path+"/pattern/"+pat, o=res_path + graph_name, time_out=time_out)
                                    op=con1.compile_re(j=jstyle, drop_unsupported=" ", r=pattern_path,  p=payload_path, o=res_path+graph_name,target=trgt, time_out=time_out)
                                print ("first check point")
                                if mem == "rbm":
                                    print("FFA :rbm")
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", r=pattern_path,  p=payload_path, o=res_path + graph_name, target=trgt, no_exm=" ", s="1500", time_out=time_out)
                                print ("second  check point")
                                if mem == "exm":
                                    print ("FFA :exm")
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ",r=pattern_path, p=payload_path, o=res_path + graph_name, target=trgt, B="0", H="0", s="1500", time_out=time_out)
                                print ("third check point")
                                if mem == "exm_plr":
                                    print ("FFA exm_plr")
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ",  r=pattern_path, p=payload_path, o=res_path + graph_name, target=trgt, B="0", H="0", L=" ", s="1500", time_out=time_out)
                                print("fourh checkpoint")
                                if mem == "rbm_exm":
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", r=pattern_path,   p=payload_path, o=res_path + graph_name, target=trgt,B="10", H="10", s="1500", time_out=time_out)
                                if mem == "rbm_exm_plr":
                                    print ("FFA:rbbm_exm_plr")
                                    op = con1.compile_re(j=jstyle, drop_unsupported=" ", r=pattern_path,  p=payload_path, o=res_path + graph_name, target=trgt, B="10", H="10", L=" ", s="1500", time_out=time_out)

                        except Exception as e:
                            op = (False, 'TIMEOUT', '0.0')
                            fun_test.log("Compilation failed")
                        actual_op = op[1]
                        con1.logger.log("op is :")
                        con1.logger.log(op)
                        time_size = ""
                        graph_sz = ""
                        compile_time = ""
                        if op[0] is True :
                            con1.logger.log("when the op[0] is true")
                            con1.logger.log("id op[0] is true")
                            fun_test.log("if op[0] is TRUE")
                            compiler_output=op[1]
                            op1=compiler_output.split("HERE ARE THE FINAL ANSWERS")[-1]
                            try:
                                compiler_output_dict=con1.create_exp_file(op1,payload_len)
                            except:
                                 con1.logger.log("failed to create the expected output dict")
                            graph_sz = op[3]
                            compile_time = op[2]
                            expected_ext_file_path=exp_file_path+base+"_"+str(idx+1)+"_exp.json"
                            print ("expected_ext_file_path",expected_ext_file_path)
                            fun_test.log("exp file name is ")
                            fun_test.log(expected_ext_file_path)
                            with open(expected_ext_file_path) as json_file:
                                data = json.load(json_file)
                                res=eval(json.dumps(data["expected"]))
                                string1=""
                                if data["expected"]==[]:
                                    string1="NO MATCH RESULTS FOUND"
                                print("res is ",res)

                                #print(type[data],type(data["expected"]))
                                print("expected_output_dict is",compiler_output_dict)
                                print ("compiler_output_dict[expected] is",compiler_output_dict["expected"])
                                fun_test.log("compiler generated match result")
                                con1.logger.log(compiler_output_dict["expected"])
                                con1.logger.log("number of compiler match results are ")
                                con1.logger.log(len(compiler_output_dict["expected"]))
                                con1.logger.log("expected file results are")
                                con1.logger.log(res)
                                con1.logger.log("number of expected match results are ")
                                con1.logger.log(len(res))
                                if  not cmp(compiler_output_dict["expected"],res):
                                    validation=True
                                    print ("validation :passed")
                                else:
                                    validation=False
                                    print ("validation:failed")
                            time_size = " graph size:" + graph_sz + " compilation time:" + compile_time
                            try:
                                string2=""
                                if op[1] =="could not find answers":
                                    print ('inside try block for op[1]==could not find the answers')
                                    string2="NO MATCH RESULTS FOUND"
                            except:
                                print ("not a empty results")

                        result_str = "Compile: (" + strategy + " Strategy) " + RegexTemplate.mem_dict[mem] +" ,Pattern" ": " + base + '.pat'  +",Payload"+pld+ "=> " + build + time_size+string2
                        print ("result_str",result_str)
                        result_str1="Validation (" + strategy + " Strategy) " + RegexTemplate.mem_dict[mem] + " ,Pattern " ": " + base + '.pat' + ",Payload : " +pld+ ",RESULT :"+ str(validation)+string1
                           # con1.create_json(pat_pld_files,exp_file_path,dfa_pc_map,nfa_pc_map,res_path,excludef_lst)
                        try:
                            if op[0] is False:
                                con1.logger.log("when op[0] is false")
                                if 'TIMEOUT' in op[1]:
                                    result_str += 'TIMEOUT'
                                else:
                                    fail_op_lst = op[1].split("\n")
                                    result_str += "".join(fail_op_lst[-5:])
                            try:
                                fun_test.test_assert(op[0],result_str + "\n")
                            except:
                                compilation_failed+=1
                            try:
                                fun_test.test_assert(validation,result_str1+"\n")
                            except:
                                validation_failed+=1
                            print ("after assertion")

                            #fun_test.test_assert(op[0], result_str + "\n")
                        except:
                            pass

            fun_test.test_assert(compilation_failed==0,' Compilation Failed testcases number: {}'.format(compilation_failed))
            fun_test.test_assert(validation_failed==0,"validation failed testcases number: {}".format(validation_failed))

        '''
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
                        validte_str = ""
                        try:
                            if (len(compare_lst) != 0):
                                validate_str = "   \nActual: " + str(sorted(actual_op)) + "Expected: " + str(sorted(exp_op))
                            fun_test.test_assert(len(compare_lst) == 0,
                                                 "Validate:" + mem + ":" + pld + "=> " + validate_str)
                        except:
                            pass
        '''
        @fun_test.safe
        def compile_only(self, mem_dist, pat_path, res_path, exclude_lst=[], engine="", juniper_style="", target="", time_out=2 * 60):
            pat_files_dict = []
            base = ""
            jstyle = "yes"
            trgt = "f1"
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

            if target == "s1":
                trgt = "s1"

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
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=ptrn,p=pat_path+pld,
                                                         o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=target)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", B="0", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", B="0", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out,target=trgt)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)

                            elif engine == "1":
                                if mem == "dflt":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", e=engine, r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="0", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", e=engine, r=ptrn,
                                                       o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", H="10", L=" ", e=engine,
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)

                            else:
                                if mem == "dflt":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", no_exm=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="0", H="0", L=" ", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm_exm":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", r=ptrn,
                                                        o=res_path + graph_name, time_out=time_out, target=trgt)
                                if mem == "rbm_exm_plr":
                                    op = self.compile_re(j=jstyle, drop_unsupported=" ", B="10", H="10", L=" ",
                                                        r=ptrn, o=res_path + graph_name, time_out=time_out, target=trgt)

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
        def validate_matches(self, actual_lst = [], expected_lst =[]):
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

