for i in range(20):
    with open("s%s-commands.txt"%str(i),"w+") as f:
        f.write("mirroring_add 1 11\n")
        f.write("table_add routeid_fwd my_drop 0 =>\n")
        f.write("table_set_default update_clone_flag updt_flg\n")
        f.write("table_set_default remove_additional_header rmv_header\n")
        f.write("table_set_default clone_to_controller c2c\n")
        f.write("table_set_default check_register checkregister")
        f.close()
