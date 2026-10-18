def apply(board):
    exact={t.m_Uuid.AsString():t for t in board.GetTracks()};ledger=[];added=[]
    def edit(uid,net,start,end,old_start,old_end):
        t=exact[uid]
        if t.GetNetname()!=net or tuple(t.GetStart())!=tuple(vec(old_start))or tuple(t.GetEnd())!=tuple(vec(old_end)):
            raise ValueError('Exact reviewed retained route precondition changed '+uid)
        old=identity(t);t.SetStart(vec(start));t.SetEnd(vec(end))
        ledger.append(dict(uuid=uid,before=old,after=identity(t),net=net,reason='Exact package functional isolation gap correction'))
    def new(model_uid,start,end):
        original=exact[model_uid];t=pcbnew.PCB_TRACK(board);t.SetNet(original.GetNet())
        t.SetLayer(original.GetLayer());t.SetWidth(original.GetWidth());t.SetStart(vec(start));t.SetEnd(vec(end));board.Add(t)
        added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
    sda='/motherboard_safety_sensor/DIC_SENSOR_SDA';scl='/motherboard_safety_sensor/DIC_SENSOR_SCL'
    edit('77ce933c-03ed-49af-a643-c0d32d5b296a',sda,[117.2,175.865],[117.2,175.865],[121.325,175.865],[121.325,175.865])
    edit('9e7ea7ed-97e0-4f74-88ae-4c8dcf999903',sda,[117.2,175.865],[118.525,175.865],[121.325,175.865],[118.525,175.865])
    edit('58c55e90-7861-467f-b6a7-3f7182708bb8',sda,[121.325,167.7071],[117.2,175.865],[121.325,167.7071],[121.325,175.865])
    edit('c09a5148-4c21-49a0-8acc-1fb04ab87d19',scl,[116.2,177.135],[116.2,177.135],[121.325,177.135],[121.325,177.135])
    edit('0e12292a-3515-4893-a3cc-764dd51fc344',scl,[116.2,177.135],[118.525,177.135],[121.325,177.135],[118.525,177.135])
    edit('268ca875-9ac6-45ff-8502-c81fd7c994c6',scl,[129.675,169],[116.2,172.5],[129.675,169],[121.325,177.135])
    new('268ca875-9ac6-45ff-8502-c81fd7c994c6',[116.2,172.5],[116.2,177.135])
    chassis='0df65ce4-7666-4119-a8ea-96e783bba855'
    edit(chassis,'/CHASSIS',[420,27.5],[414,27.5],[420,28],[414,28]);new(chassis,[420,28],[420,27.5]);new(chassis,[414,27.5],[414,28])
    mpg='ae43fd60-995c-4b41-bffb-c85530d90492'
    edit(mpg,'/motherboard_operator/MPG_SEL_Y',[89.8821,301],[102.25,302],[89.8821,296.7071],[102.25,302]);new(mpg,[89.8821,296.7071],[89.8821,301])
    cond='075108d5-7295-4d62-8794-a06af67d0347'
    edit(cond,'/motherboard_operator/MPG_SEL_Y_CONDITIONED',[93.71997,288.3],[106.3375,288.3],[93.71997,291.35],[106.3375,291.35]);new(cond,[93.71997,291.35],[93.71997,288.3]);new(cond,[106.3375,288.3],[106.3375,291.35])
    fault='/motherboard_operator/PRB0_FAULT_GOOD_ISO'
    edit('d4afb6ba-ff4b-4222-8413-50264fea6d5f',fault,[102.65,294.365],[104.4,294.365],[102.65,294.365],[95.1375,294.365])
    edit('247f83ae-65ff-4227-bfd1-54e6593a66e3',fault,[104.4,302.05],[95.1375,302.05],[95.1375,294.365],[95.1375,302.05])
    new('d4afb6ba-ff4b-4222-8413-50264fea6d5f',[104.4,294.365],[104.4,302.05])
    ao='/motherboard_acc_control/AO_I2C_SDA_HOST'
    edit('0cd3817e-fb12-44b4-9f87-0a20e04bdab8',ao,[413.03003,254.87003],[409,245],[413.03003,254.87003],[413.03003,241.35997])
    edit('7f769cc1-832d-4d0c-90da-f6ec781a0190',ao,[409,245],[410.01997,241.35997],[413.03003,241.35997],[410.01997,241.35997])
    return ledger,added
