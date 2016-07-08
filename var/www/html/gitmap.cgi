#!/bin/bash
#portal


[ "x$INC_BASE" == "x" ] && INC_BASE="/usr/lib/bps"
source $INC_BASE/base.inc $*

SEP="@-"
SEP1="@,"
SEP_PATH="/"

export LANG=c


BD="/var/www/html/data/gitmap"


function hex2bin(){
    export LANG=c
    awk '
BEGIN{
  for(i=0;i<256;i++){
     j=sprintf("%02x",i);
     map[toupper(j)]=i;
  }
}
{
 
 len=length($1);
 len=len/2;

 c=toupper($1);
 for(i=1;i<=len;i++){
  printf("%c",map[substr(c,(i-1)*2+1,2)]);
 }
}'

}

function bin2hex(){
    od -t x1 | awk '{for(i=2;i<=NF;i++) printf("%s",toupper($i));}'
}


function import_html_lib(){
    cat<<EOF
  <link rel="stylesheet" href="/hr/jquery-ui/jquery-ui.css">
  <script src="/hr/jquery.min.js"></script>
  <script src="/hr/jquery-ui/jquery-ui.js"></script>    
EOF
}

#sync to awklib path_encode()
function path_encode(){
    sed "s| |@SPACE@|g"
}

#sync to awklib path_decode()
function path_decode(){
    sed "s|@SPACE@| |g"
}

function file_wrap_for_xargs(){
    sed "s|^|\'|;s|$|\'|"
}

function get_log_parse(){
    repo_enter
    git -c core.quotepath=off  log --format="%H %ci%n%B%nBODY_END"   --raw | awk '
BEGIN{
    n=0
}
{
    if(NF>0) lines[n++]=$0;
}
END{
    i=0;
    while(i<n){
        split(lines[i],a);
        commit=a[1];
        date=a[2]
        time=a[3];
        body="";
        i++;
        while(i<n){
            if(lines[i] == "BODY_END"){
                break;
            }
            if(body){
                body=sprintf("%s %s",body,lines[i])
            }else body=lines[i];
            i++;
        }
        i++;
        while(i<n){
            split(lines[i],a);
            if(a[1] ~/^:/){
                break;
            }
            i++;
        }
        while(i<n){
            split(lines[i],a);
            if(a[1] !~/^:/){
                break;
            }


            i++
        }
        print "#",commit,date,time,body
    }
}
'
    repo_exit   
}

function link_env(){
    local codes='
BEGIN{
    getline
    for(i=1;i<=NF;i++){
        n=split($i,a,"=");
        if(n==2){
            ENVIRON[a[1]]=a[2];
        }
    }
    parse_opt();
    print link_env();

}'
  echo $* |  awk  "`gitmap_lib` $codes"

}

function repo_enter(){
    [ "x$OPT_REPO" != "x" ] && pushd $OPT_REPO > /dev/null
}

function repo_exit(){
    [ "x$OPT_REPO" != "x" ] && popd > /dev/null    
}


#function base
function list_mm_file_by_find(){
    local base=$1
    [ "x$base" == "x" ] && base="$OPT_REPO"
    find -L "$base" -name "*.mm" | path_encode
}


#function base
function list_graph_file_by_find(){
    local base=$1
    [ "x$base" == "x" ] && base="$OPT_REPO"
    find -L "$base" -type f -iregex ".*\.dot\|.*\.mm" | path_encode
}



function list_mm_file_by_auto(){
    [ "x$OPT_REPO" == "x" ] && return;
    repo_enter
    local check=`git rev-parse --is-bare-repository 2>/dev/null`
    if [ "x$check" == "xtrue" ];then
        git  -c core.quotepath=off ls-tree --full-tree --name-only -r HEAD|grep "\.mm$" | sort |path_encode
    else
        find -L  -name "*.mm" | sort -u |sed "s|^\./||"| path_encode        
    fi
    repo_exit
}

function list_mm_file_with_commit(){
    repo_enter
    local i;
    list_mm_file_by_auto | while read i;do
       echo "$i"|path_decode|file_wrap_for_xargs|xargs git -c core.quotepath=off log --format="%H"  --follow --|sed "s|^|$i |"
    done
    repo_exit
}

function list_mm_file_from_repo(){
    [ "x$OPT_REPO" == "x" ] && return;
    repo_enter
    local commit="HEAD"
    #[ "x$OPT_COMMIT" != "x" ] && commit=$OPT_COMMIT
    git  -c core.quotepath=off ls-tree --full-tree --name-only -r $commit | grep "\.mm$" | path_encode
    repo_exit
}


function git_log_OPT_FILE(){
    repo_enter
    echo $OPT_FILE|path_decode|file_wrap_for_xargs|xargs git -c core.quotepath=off log --format="commit %H %ci"  --follow --date=iso --name-only --|awk '{if(NF>0) print $0}'
    repo_exit   
}


#function base
function git_log_repo_mm_files(){
    local base=$1
    [ "x$base" == "x" ] && base="$OPT_REPO"

    [ "x$base" == "x" ] && return;

    [ "x$base" != "x" ] && pushd $base > /dev/null
    {
        git log --date=iso|awk '/^commit/ { print $2}' | while read i;do
            git -c core.quotepath=off show --pretty="format:" --name-only $i --date=iso| grep "\.mm" | path_encode | head -1 | sed "s|^|$i |"
        done | awk '{print "#1",$1}' 
        git log --date=iso
    } | awk '
{
    if($1 == "#1"){
        m[$2]=1
    }else{
        if($0 ~/^commit/){
            p=0;
            if(m[$2]==1){
                p=1
            }
        }
        if(p==1) print $0
    }

}'

#    if [ -d "$OPT_REPO/.git" ];then
#        echo `find -L "$OPT_REPO" -name "*.mm"|sed "s|$OPT_REPO||;s|^/||" | file_wrap_for_xargs `| xargs git log --date=iso 
#    elif [ -f $OPT_REPO/HEAD ];then
#        git -c core.quotepath=off show --pretty="format:" --name-only $OPT_COMMIT|grep "\.mm"|path_encode| xargs git log --date=iso 
#    fi
    [ "x$base" != "x" ] && popd > /dev/null
}


#function key [defaultvalue]
function parse_argv(){
  [ "x$1" == "x" ] && return;
  local key=$1
  local dft=$2

  awk -vkey=${key} -vdft=${dft} '
{

     for(i=1;i<=NF;i++){
         idx=index($i,"=");
         if(idx>0){
           a=substr($i,1,idx-1);
           b=substr($i,idx+1);
           if(key == a){
              dft=b;
           }
         }
     }
}
END{
  print dft
  }'
}

function html_get_mm_file(){
  html_response_type "text/html"
  get_mm_file
}

function get_mm_file(){
    if [ "x$OPT_REPO" == "xLOGINFO" ];then
	generate_dot_file
	return
    fi
    if [ "x$1" != "x" ] && [ -f "$1" ];then
        cat "$1"
        return;
    fi

    local useGit="";
    local f="";

    [ "x$OPT_REPO" == "x" ] && return;

    [ "x$OPT_FILE_HEX" != "x" ] && OPT_FILE=`echo $OPT_FILE_HEX|hex2bin`
    [ "x$OPT_REAL_FILE_HEX" != "x" ] && OPT_REAL_FILE=`echo $OPT_REAL_FILE_HEX|hex2bin`

    [ ! -d "$OPT_REPO/.git" ] && useGit="y"
    [ "x$OPT_COMMIT" != "x" ] && useGit="y"

    if [ "x$useGit" == "x" ];then
        f=`echo $OPT_REPO/$OPT_FILE|path_decode`
        if [ -f "$f" ];then
            cat "$f"
            return;
        fi
    fi

    local commit="HEAD"
    [ "x$OPT_COMMIT" != "x" ] && commit=$OPT_COMMIT

    if [ "x$OPT_REAL_FILE" != "x" ];then
        f=`echo $OPT_REAL_FILE|path_decode`
    else
        f=`echo $OPT_FILE|path_decode`
    fi

    if [ "x$OPT_COMMIT" == "x" ];then
      repo_enter
      if [ -f "$f" ];then
        cat "$f"
        repo_exit
        return;
      fi  
      repo_exit
    fi

    repo_enter
    git show "$commit:$f"
    repo_exit
    

}

function show_html_options(){
    cat $0|sed "s|[\"=()\${}&!,/:\\|\[]| |g;s|]| |g" | awk '{for(i=1;i<=NF;i++){if($i ~/^OPT_/) print $i}}'|sort -u
}


function gitmap_lib(){
  echo '
 #ex array,"1nr 2"
 function sort_lines(array,ops,sep,    a_ops,m_ops,i,n,i1,n1,prefix,a,idx){
    n=split(ops,a_ops,"[[:space:]]*")
    for(i=1;i<=n;i++){
        m_ops[gensub("[[:alpha:]]","","g",a_ops[i])] =     gensub("[[:digit:]]","","g",a_ops[i]);
    }
    for(i1 in array){
        n1=split(array[i1],a,sep)
        prefix=""
        for(i=1;i<=n;i++){
            idx=gensub("[[:alpha:]]","","g",a_ops[i])
            if(m_ops[idx] == "n"){
                prefix= prefix sprintf("%010d",a[idx])
            }else if(m_ops[idx] == "r"){
                #TODO
                prefix= prefix sprintf("%-50s",a[idx])
            }else if(m_ops[idx] == "nr" || m_ops[idx] == "rn"){
                prefix= prefix sprintf("%010d",10000000000 - a[idx])
            }else{
                prefix= prefix sprintf("%-50s",a[idx])
            }
        }
        array[i1]= prefix sprintf("%10d",i1)  "##@@##" array[i1]
    }
    asort(array);
    n=length(array);
    for(i=1;i<=n;i++){
        array[i]=gensub(".*##@@##","","",array[i])
    }
    return n;
 }
   
 function url_decode(x, hextab,decoded,i,len,c,c1,c2,code){
   hextab ["0"] = 0; hextab ["8"] = 8;
   hextab ["1"] = 1; hextab ["9"] = 9;
   hextab ["2"] = 2; hextab ["A"] = hextab ["a"] = 10
   hextab ["3"] = 3; hextab ["B"] = hextab ["b"] = 11;
   hextab ["4"] = 4; hextab ["C"] = hextab ["c"] = 12;
   hextab ["5"] = 5; hextab ["D"] = hextab ["d"] = 13;
   hextab ["6"] = 6; hextab ["E"] = hextab ["e"] = 14;
   hextab ["7"] = 7; hextab ["F"] = hextab ["f"] = 15;
   decoded = ""
   i   = 1
   len = length (x)
   while ( i <= len ) {
   c = substr (x, i, 1)
   if ( c == "%" ) {
   if ( i+2 <= len ) {
    c1 = substr (x, i+1, 1)
    c2 = substr (x, i+2, 1)
    if ( hextab [c1] == "" || hextab [c2] == "" ) {
     print "WARNING: invalid hex encoding: %" c1 c2 | "cat >&2"
   } else {
    code = 0 + hextab [c1] * 16 + hextab [c2] + 0
    c = sprintf ("%c", code)
    i = i + 2
   }
   } else {
    print "WARNING: invalid % encoding: " substr ($0, i, len - i)
   }
   } else if ( c == "+" ) {
    c = " "
   }
   decoded = decoded c
   ++i
   }
   return decoded
 
 }

 function path_encode(x){
    return gensub("[[:space:]]","@SPACE@","g",x);
 }

 function path_decode(x){
    return gensub("@SPACE@"," ","g",x);
 }

 function path_format1(x){
    return gensub(".*/","","",x);
 }

 function path_format_by_setting(x, f,d){
    if(OPT_WIDGET_BEAUTY_PATH){
        f=gensub(".*/","","",x);
        d=gensub("/" f,"","",x);
        return gensub(".*/","","",x) "&nbsp;[" d  "]";
    }else{
        return x;
    }
 }

 function ENV(key, value){
    if(key in ENVIRON){
        value=url_decode(ENVIRON[key]);    
    }
    if(key == "OPT_WIDGET_TIME2COLOR_TIME" && !value){
        return 1;
    }
    return value;
 }
 function parse_opt_post(dft,i){
    if("OPT_WIDGET_TIME2COLOR_THEME" in ENVIRON){} else  OPT_WIDGET_TIME2COLOR_THEME="color7"
    if("OPT_WIDGET_TIME2COLOR_METHOD" in ENVIRON){} else OPT_WIDGET_TIME2COLOR_METHOD="group"
    if("OPT_WIDGET_TIME2COLOR_TIME" in ENVIRON){} else   OPT_WIDGET_TIME2COLOR_TIME=86400000
    if(!OPT_WIDGET_TIME2COLOR_TIME) OPT_WIDGET_TIME2COLOR_TIME=1;
 }

function link(m,   k){
    url="?fun="
    if("OPT_FUN" in m){
        url=url m["OPT_FUN"]
    }else{
        url=url OPT_FUN
    }
    for(k in m){
        url=url "&" k "=" m[k]
    }
    return url
 } 

 function link_env(m,   k,a){
    url="?fun="
    if("OPT_FUN" in m){
        url=url m["OPT_FUN"]
    }else{
        url=url OPT_FUN
    }
    for(k in ENVIRON){
        if(k ~/^OPT_/ && k != "OPT_FUN"){
            a[k]=1;
        }
    }    
    for(k in m){
        a[k]=1;
    }

    for(k in a){
        if(k in m){
            url=url "&" k "=" m[k]
        }else{
            url=url "&" k "=" ENVIRON[k]
        }
    }
    url=url "&OPT_T=" systime(); 
    return url
 }

 '

 env|awk -F = '
BEGIN{
    print "function parse_opt(){"
}
/^OPT_/{
    printf("%s=ENVIRON[\"%s\"]\n",$1,$1)

}
END{
    print "parse_opt_post()"
    print "}"
}'


}

function fix_dot_format(){
    sed "s|&apos;|\'|"
}

function freemind2dot(){
    local codes='

 function print_node(id, gid,text,m){
    gid=id
    id=gensub("__m","","",id);
    m=index(gid,"__m");
    text=NODE_TEXT[id]
    if(m){
        text = "*"text;
    }
    if(!OPT_WIDGET_EXPNAD_FOLDER && NODE_FOLDED[id]){
        text= "[" text "]"
    }
    printf("\"%s\" [ tooltip=\"%s\" label=\"%s\",fontcolor=\"%s\",width=0.02,height=0.2,shape=\"plaintext\" ,margin=\" 0.0,0.0\" ];\n",gid,strftime("%Y-%m-%d %H:%M:%S ",NODE_CREATED[id]/1000) "|" strftime("%Y-%m-%d %H:%M:%S ",NODE_MODIFIED[id]/1000) ,text,get_color(NODE_CREATED[id]));
 }

 function print_line(id){
    printf("\"%s\" -> \"%s\" [size=.1,arrowsize=\"0.1\",color=\"%s\",style=\"dashed\"] ;\n",NODE_PARENT[id],id,get_color(NODE_MODIFIED[id]));           
 }


function handle_time2color(a_time,type,  t,a1,b1,i,idx,last){
   t=OPT_WIDGET_TIME2COLOR_TIME
   if(OPT_WIDGET_TIME2COLOR_METHOD == "group"){
       for(i in a_time){
           a1[10000000000000-i]=a_time[i];
       }
       asort(a1);
       i=1;
       last=0;
       idx=0;
       while(i<=length(a1)){
           if( (a1[i] - last) > t){
               idx++
           }
          # print "#0",i,t,a1[i]-last,idx
           b1[a1[i]]=idx
           
           last=a1[i];
           i++;
       }
       for(i in a_time){
           a_time[i]=b1[i];
          # print "#1",i,a_time[i],b1[i]
       }
       NTT=length(a1);
       return;
   }
   for(i in a_time){
       a1[int(a_time[i]/t)]=int(a_time[i]/t);
   }
   for(i in a1){
        a1[i]=sprintf("%d#%d",10000000000000-i,i);
   }
   asort(a1);
   for(i=1;i<=length(a1);i++){
    b1[gensub(".*#","","",a1[i])]=i
   }
   NTT=length(a1);
   for(i in a_time){
       a_time[i]=b1[int(a_time[i]/t)];
   }
}

 function get_color_by_index(i){
    # print "#1",NTT,NCOLOR,i,int((i-1)*NCOLOR/NTT)+1
    if(i>NCOLOR) i=NCOLOR;
    if(i == 0 || NCOLOR == 0){ return "black";}    
    if(NTT <= NCOLOR/3 && NTT > 0){
        return COLOR[int((i-1)*NCOLOR/NTT)+1];    
    }
    return COLOR[i];
    
}
 function get_color(t,  i){
    i=int(TT[t]);
    return get_color_by_index(i);
 } 

 function print_graph_main(){
    if(OPT_CLUSTER){
        for(id in NODE_ID_CENTER){
            print_node(id)
        }
        
        print "subgraph cluster_left {";
        for(id in NODE_ID_LEFT){
            print_node(id)
        }
        print "}"
        
        print "subgraph cluster_right {";
        for(id in NODE_ID_RIGHT){
            print_node(id)
        }
        print "}"        
    }else if(OPT_PART){
        if(OPT_PART=="left"){
            for(id in NODE_ID_CENTER){
                NODE_TEXT[id]=""
                print_node(id);
            }

            for(id in NODE_ID_LEFT){
                print_node(id);
            }
        }
         if(OPT_PART=="right"){
            for(id in NODE_ID_CENTER){
                NODE_TEXT[id]=gensub("[[:space:]][[:space:]]*","\\\\l","g",NODE_TEXT[id]);
                print_node(id);
            }
            for(id in NODE_ID_RIGHT){
                print_node(id);
            }
        }       
    }else{
        for(id in NODE_ID){
            print_node(id);
        }
    }
    
    for(id in NODE_ID){
        if(NODE_PARENT[id]){
            pid=NODE_PARENT[id]
            if(!OPT_PART ||\
             (OPT_PART=="left"  && NODE_ID_LEFT[id]  && (NODE_ID_LEFT[pid] ||NODE_ID_CENTER[pid])) ||\
             (OPT_PART=="right" && NODE_ID_RIGHT[id] && (NODE_ID_RIGHT[pid]||NODE_ID_CENTER[pid]))){
                if(!OPT_GRAPH_TIMELINE)
                 print_line(id);
            }
        }
    }

 }
 
BEGIN{
    #NODE_XXX,COLOR,NCOLOR,COLOR_TABLE
    
    COLOR_TABLE["gray"]="gray0"
    for(i=3;i<=60;i+=3) COLOR_TABLE["gray"]=sprintf("%s gray%d",COLOR_TABLE["gray"],i); 

    COLOR_TABLE["gray7"]="gray0"
    for(i=7;i<=60;i+=7) COLOR_TABLE["gray7"]=sprintf("%s gray%d",COLOR_TABLE["gray7"],i); 
    

    COLOR_TABLE["color"]="red4 red3 red2 red1 red"\
    " orange4 orange3 orange2 orange1 orange"\
    " yellow4 yellow3 yellow1 yellow"\
    " green4 green3 green2 green1 green"\
    " cyan4 cyan3 cyan2 cyan1 cyan"\
    " blue4 blue3 blue2 blue1 blue"\
    " purple4 purple3 purple2 purple1 purple"

    COLOR_TABLE["color7"]="red orange yellow4 green cyan blue purple"

   
    parse_opt();

    if(OPT_PART == "left"){
        OPT_RANKDIR="RL"
    }

    NCOLOR=split(COLOR_TABLE[OPT_WIDGET_TIME2COLOR_THEME],COLOR,"[[:space:]][[:space:]]*");

    #skip two line
    getline; 
    getline;
    dn=1;
    cn=1;
    parse_tree(0)
    
    for(t in NODE_CREATED){
        TT[NODE_CREATED[t]]=NODE_CREATED[t];
    }
    for(t in NODE_MODIFIED){
        TT[NODE_MODIFIED[t]]=NODE_MODIFIED[t];
    }

    handle_time2color(TT)
 
    print "digraph G {"
    if(OPT_RANKDIR){
        print "rankdir=" OPT_RANKDIR ";"
    }else{
        print "rankdir= LR;"
    }
    print "rank=\"min\";"
    print "ranksep=0.1;"
    print "pad=0.01;nodesep=0.04;"
    print "arrowhead=\"none\"";
    print "node ["
    print "    fontname = \"Bitstream Vera Sans\""
    print "    fontsize = 12"
    print "]"
    





    if(OPT_GRAPH_TIMELINE){
        max=1
        for(k in NODE_ID){
            t=NODE_CREATED[k];
            i=TT[t];
           !IDX_2_TIME[i] && IDX_2_TIME[i]=t;   
            IDX_2_IDS[i]=IDX_2_IDS[i]?IDX_2_IDS[i] "," k:k

            t=NODE_MODIFIED[k];
            i=TT[t];
           !IDX_2_TIME[i] && IDX_2_TIME[i]=t;   
            IDX_2_IDS[i]=IDX_2_IDS[i]?IDX_2_IDS[i] "," k"__m":k"__m"

            print_node(k)
            if(OPT_WIDGET_SHOW_MODIFIED){
                print_node(k"__m")                
            }
        }



        for(idx in IDX_2_IDS){
#            print "#0",idx,IDX_2_IDS[idx]
            s=IDX_2_IDS[idx]
            n=split(s,a,",");
            print "{rank=same;"
            printf("color_timeline%d ",idx)
            for(i=1;i<=n;i++){
                if(OPT_WIDGET_SHOW_MODIFIED || index(a[i],"__m") == 0){
                    printf("%s ",a[i]);
                }
            }
            print "}"

            n=split(idx,b,"__")
            if(n==2){
                TT_MODIFIED[b[1]]=idx;
            }else{
                TT_CREATED[idx]=idx;    
            }
            TT1[idx]=sprintf("%10d",idx)

            print "#1",idx,IDX_2_IDS[idx]
        }

        n=asort(TT1);
        
        for(j=1;j<=n;j++){
           i=int(TT1[j]) 
           lable=strftime("%Y-%m-%d\\l%H:%M:%S ",IDX_2_TIME[i]/1000);
           #lable=substr(lable,3);
           printf("\"color_timeline%d\" [ label=\"%s\",fontsize=8,fontcolor=\"%s\",shape=\"plaintext\"  ,margin=\" 0.0,0.0\",width=0.02,height=0.2 ];\n",i,lable,get_color_by_index(i));
        }
        for(j=1;j<=n;j++){
            i=TT1[j] 
            if(j!=1){
                printf(" -> ");
            }
            printf("color_timeline%d",i)        
        }
        printf(" [size=.1,arrowsize=\"0.1\",style=\"dashed\"] ;\n");
    }else{

        print_graph_main()

    }
    print "}"
}

 function S(n,i,r){
   r=""; 
   for(i=1;i<=n;i++) r=r " ";
   return r;
 }
 
 function parse_value(str,key,   i){
     i=index(str,key "=\"")
     if(i>0){
         return gensub("\".*","","",substr(str,i+length(key)+2))
     }
 }
 function parse_line(line,MAP){
    delete MAP;
    if(substr(line,1,2) != "</" && substr(line,1,1) == "<"){
        MAP["tag"]=substr($1,2);
    }
    MAP["CREATED"]=parse_value(line,"CREATED");
    MAP["ID"]=parse_value(line,"ID");
    MAP["MODIFIED"]=parse_value(line,"MODIFIED");
    MAP["POSITION"]=parse_value(line,"POSITION");
    MAP["TEXT"]=parse_value(line,"TEXT");
    MAP["FOLDED"]=parse_value(line,"FOLDED");
 }
 
 function parse_node(level,parent,current, id,m){
     
     if(OPT_GRAPH_MAX_LEVEL && level > OPT_GRAPH_MAX_LEVEL) return;
     #print S(level) current
     parse_line(current,mc)
     parse_line(parent,mp)
     
     id=mc["ID"];
     if(!id){
        id="ID_" mc["CREATED"]
     }
     if(mc["TEXT"]){
        NODE_TEXT[id]=url_decode(mc["TEXT"]);   
     }else{
        NODE_TEXT[id]="..."
     }
     NODE_CREATED[id]=mc["CREATED"]
     NODE_MODIFIED[id]=mc["MODIFIED"]
     NODE_POSITION[id]=mc["POSITION"];
     NODE_LEVEL[id]=level
     NODE_FOLDED[id]=mc["FOLDED"]

     if(OPT_GRAPH_TEXT_MAX && int(OPT_GRAPH_TEXT_MAX)>0){
       if(OPT_GRAPH_TEXT_MAX<length(NODE_TEXT[id])){
          NODE_TEXT[id]=substr(NODE_TEXT[id],1,OPT_GRAPH_TEXT_MAX) "...";  
       } 
     }

     if(mp["ID"]){
         if(!NODE_CHILDREN[mp["ID"]]){
             NODE_CHILDREN[mp["ID"]]=id;
         }else{
            NODE_CHILDREN[mp["ID"]]=NODE_CHILDREN[mp["ID"]] "," id
         }
         NODE_PARENT[id]=mp["ID"];
     }
     
     if(mc["POSITION"]){
        NODE_POSITION[id]=mc["POSITION"]
     }else{
        NODE_POSITION[id]=NODE_POSITION[NODE_PARENT[id]]
     }
     NODE_ID[id]=id
     if(NODE_POSITION[id] == "right"){
         NODE_ID_RIGHT[id]=id
     }else if(NODE_POSITION[id] == "left"){
        NODE_ID_LEFT[id]=id
     }else{
         NODE_ID_CENTER[id]=id
     }
 }
 
 #TODO parse richcontent xml
 function parse_tree(level,parent,MAP){
    while(getline){
        if($1 ~/^<\/node/){
            break;
        }else if($1 ~/^<node/){
            parse_line($0,MAP)
            if(MAP["tag"] == "node"){
                parse_node(level,parent,$0)
            }
            if($NF ~ /\/>$/){
                in_folder=0
            }else{
                parse_tree(level+1,$0);
            }
        }
    }    
 }
'


    {
        if [ "x$OPT_WIDGET_EXPNAD_FOLDER" == "x" ];then
            awk '{
    p=1;
    if($0 ~/FOLDED="true"/){
        print $0
        l=1;
        while(getline){
          #  print "#0",$0
            if($1 =="<node"){
                if($NF ~/\/>$/){

                }else{
                    l++;
                }
            }
            if($1 == "</node>"){
                l--;
            }
            if(l==0){
                print $0
                break;
            }
          #  print "#1",l
        }
    }else{
        print $0
    }
}'        
    else
        cat
    fi
    } | fix_dot_format|awk  "`gitmap_lib` $codes"
}

#function freemind_file type:[text|png|svg|svgs]
function html_freemind2dot(){
    [ "x$OPT_FILE" == "x" ] && export OPT_FILE=$1
    [ "x$OPT_GRAPH_TYPE" == "x" ] && export OPT_GRAPH_TYPE=$2

    local type=$OPT_GRAPH_TYPE

    if [ "x$type" == "xfile" ];then
        html_response_type "text/plain"
        get_mm_file 
        return
    fi
    


    if [ "x$type" == "xpng" ];then
        html_response_type "image/png"
        get_mm_file | freemind2dot |dot -T$type
        return
    fi
    

    if [ "x$type" == "xsvg" ];then
        html_response_type "text/html"
        get_mm_file | freemind2dot |dot -T$type
        return
    fi
    
    if [ "x$type" == "xdot" ];then
        html_response_type "text/html"
        get_mm_file | freemind2dot |dot
        return
    fi    

    if [ "x$type" == "xsvgs" ];then
        html_response_type "text/html"
        
        unset IS_CGI
        export OPT_PART="right"
        export OPT_GRAPH_TYPE="svg"
        local right=`html_freemind2dot`

        export OPT_RANKDIR="RL"
        export OPT_PART="left"
        local left=`html_freemind2dot`

     cat<<EOF
<html>
<body>

<table>
<tr><td>$left</td><td>$right</td></tr>
</table>
</body>
</html>     
EOF

        return
    fi
    html_response_type "text/html"
    get_mm_file | freemind2dot
}



function html_gitmap_lastest(){

    {
        find -L $BD -name "HEAD" | sort |sed "s|/.git/HEAD$||;s|/HEAD$||"| while read d;do
            git_log_repo_mm_files  $d  |awk '{printf("@@%s@##@",$0)}END{print ""}'|sed "s|@@commit|\ncommit|g"|sed "s|$|@##@$d|;s|$BD/||"
            #|sed "s|^|$d@@|;s|$BD/||"
        done

    } |awk '{print gensub(".*@##@@@Date:","","",$0) "LINE123456" $0}'|sort -u -r|sed "s|.*LINE123456||"|grep "^commit"|awk -vBD=$BD '
BEGIN{
    print "<table border=1>"

}    
{
    if($1=="commit"){
        n=split($0,a,"@##@")
        project=a[n]

        print "<tr>"
        printf("<td><a href=\"?fun=html_gitmap&OPT_REPO=%s" "&OPT_T="systime()  "\">%s</a></td>\n",BD "/" project,project);

        print "<td>"

        split(a[1],b,"[[:space:]][[:space:]]*")
        commit=b[2]
        printf("<a href=\"?fun=html_gitmap&OPT_REPO=%s&OPT_COMMIT=%s" "&OPT_T="systime()  "\">\n",BD "/" project,commit);
        print "<div><pre>"
        for(i=3;i<n;i++){
            print gensub("^@@","","",a[i])
        }
        print "</pre></div>"
        print "</a>"
        print "</td>"

    }


}
END{
    print "</table>"
}'
}

function find_dirs(){
  find $* |egrep -v "/\.git/"|sed "s|/[^/]*$||"|sort -u | awk '
BEGIN{
  n=0;
}    
{
 t=1;
 for(i=0;i<n;i++){
   if(index($0,p[i] "/")>0){
     t=0;
     break;
   }
 }
 if(t!=0){
  print $0;
  p[n++]=$0
 }
}' 
}

function html_gitmap_noargs(){
    html_response_type "text/html"

    cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
</head>
<body>
EOF

    echo "<div style=\"float:left\">"

    find_dirs -L  $BD -iregex ".*\.mm\|.*\.dot\|.*/HEAD"| while read i;do
         local git=$i
         local project=`basename $i` 
#         echo "<h3><a href=\"?fun=html_gitmap&OPT_REPO=$git\">$project</a></h3>"

         awk -vgit="$git" -vproject="$project" 'BEGIN{ printf("<h3><a href=\"?fun=html_gitmap&OPT_REPO=%s" "&OPT_T="systime()  "\">%s</a></h3>",git,project)}'

         list_graph_file_by_find $i| awk -vbase="$i" '
{
    git=base
    file=substr($0,length(git)+1)
    file=gensub("^/","","",file);
    title=gensub(".*/","","",$1);

    f="html_gitmap"
    if($0 ~/\.dot$/){
      f="html_gitdot"
    }
    printf("&nbsp;<a href=\"?fun=%s&OPT_REPO=%s&OPT_FILE=%s" "&OPT_T="systime()  "\">%s</a><br/>\n",f,git,file,title)
    
    l=git
}'
    done

    echo "</div>"

    echo "<div style=\"float:right\">"
    html_gitmap_lastest
    echo "</div>"

    cat<<EOF
</body>
</html>
EOF
}


#name
function html_widget_head(){
    local name=$1
    cat<<EOF
<div class="widget widget_$name">
EOF
}

function html_widget_tail(){
    echo "</div>"
}

#function name style= onchange= lable= value=
function gitmap_widget_select(){
    
    local name=$1
    local style=`echo $*|parse_argv style|url_decode`
    local onchange=`echo $*|parse_argv onchange|url_decode`
    local lable=`echo $*|parse_argv lable|url_decode`
    local title=`echo $*|parse_argv title|url_decode`
    local value=`echo $*|parse_argv value|url_decode`
    local scripts="";
    if [ "x$onchange" != "x" ];then
        scripts=`$onchange`
    fi
    

        local codes='
BEGIN{
    parse_opt()
    if(name in ENVIRON){
        dft=ENVIRON[name]
    }else{
        dft=value
    }
}  
{
    attr="";
    if(dft==$1){
        attr="selected=\"selected\""
    }
    printf("<option %s value=\"%s\">%s</option>\n",attr,$1,$2)
}
'

    [ "x$lable" != "x" ] && echo "$lable:"
    cat<<EOF
<select name="$name" style="$style" title="$title" onchange='$scripts'>
  <option value="">--</option>
EOF

    awk -F "|" -vname=$name -vvalue=$value "`gitmap_lib` $codes" 
    
    cat<<EOF
 </select>
EOF

}

#function name dft_value lable= title
function gitmap_widget_textfiled(){
  local name=$1
  local title=`echo $*|parse_argv title|url_decode`
  local lable=`echo $*|parse_argv lable|url_decode`
  local rlable=`echo $*|parse_argv rlable|url_decode`
  local dft_value=`echo $*|parse_argv value|url_decode`
  local onchange=`echo $*|parse_argv onchange|url_decode`
  local size=`echo $*|parse_argv size|url_decode`

  local value;
  if env |grep "^OPT_SUBMIT=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
  else
    value=$dft_value
  fi

  local scripts="";
  if [ "x$onchange" != "x" ];then
    scripts=`$onchange`
  fi
  local size_html="";
  [ "x$size" != "x" ] && size_html="size=$size"
  cat<<EOF
$lable<input $size_html id="$name" type="input" name="$name" value="$value" title="$title" onChange='$scripts'>$rlable
EOF

}

#function name dft_value lable= title
function gitmap_widget_checkbox(){
  local name=$1
  local dft_value=$2
  local title=`echo $*|parse_argv title|url_decode`
  local lable=`echo $*|parse_argv lable|url_decode`
  local onclick=`echo $*|parse_argv onclick|url_decode`

  local value;

  if env |grep "^OPT_SUBMIT=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
  else
    value=$dft_value
  fi

  local html_checked;
  if [ "x$value" == "xon" ]  || [ "x$value" == "xON" ];then
    html_checked="checked=\"true\""
  fi

  local scripts="";
  if [ "x$onclick" != "x" ];then
    scripts=`$onclick`
  fi
  cat<<EOF
<input id="$name" type="checkbox" name="$name" $html_checked title="$title" onclick='$scripts'>$lable
EOF

}


#function name value= lable= title=
function gitmap_widget_button_change_value(){
  local name=$1
  local dft_value=$2
  local value=`echo $*|parse_argv value|url_decode`
  local title=`echo $*|parse_argv title|url_decode`
  local lable=`echo $*|parse_argv lable|url_decode`
  local onclick=`echo $*|parse_argv onclick|url_decode`

  local scripts=`
  {
    cat<<EOF
e=document.getElementById("$name");if(e) e.value="$value";document.getElementById("main_form").submit();
EOF
  }`

  [ "x$onclick" != "x" ] && scripts=`$onclick`

  cat<<EOF
  <button title="$title" onclick='$scripts'>$lable</button>
EOF

}
function html_gitmap_js_form_submit(){
    cat<<EOF
document.getElementById("main_form").submit()
EOF
}


function html_gitmap_form_head(){

    cat<<EOF
<form id="main_form" action=""  method="get">
EOF

}

function html_gitmap_form_tail(){
   
    local codes='
BEGIN{
    parse_opt()
    s="OPT_FUN OPT_WIDGET_NAV OPT_WIDGET_BODY OPT_WIDGET_TIMELINE OPT_GRAPH_MAX_LEVEL OPT_GRAPH_TEXT_MAX"
    n=split(s,a);
    for(i=1;i<=n;i++) b[a[i]]=1
    for(k in ENVIRON){
        if(k ~/^OPT_/ && !b[k] && k !~/^OPT_WIDGET_/){
          printf("<input type=\"hidden\" id=\"%s\" name=\"%s\" value=\"%s\">",k,k,url_decode(ENVIRON[k]))            
        }
    }

    s=""
    n=split(s,a);
    for(i=1;i<=n;i++){
        k=a[i];
        if(k in ENVIRON){

        }else{
            printf("<input type=\"hidden\" id=\"%s\" name=\"%s\" value=\"\">",k,k)                
        }
    }

}'

   awk  "`gitmap_lib` $codes"

    cat<<EOF
</form>
EOF
}


function html_gitmap_widget_nav(){
    
    html_widget_head nav

    cat<<EOF
<input type="hidden" name="fun" value="$OPT_FUN">
<input type="hidden" name="OPT_SUBMIT" value="">

<table>
<tr>
  <td>
    <a href="?fun=$OPT_FUN">[More Files]</a>
    <a href="?fun=$OPT_FUN&OPT_REPO=$OPT_REPO&OPT_FILE=$OPT_FILE">[Clear]</a>
  </td>
  <td>
    `gitmap_widget_checkbox OPT_WIDGET_MORE lable=[Widgets%20Setting]  title=show%20widgets onclick=html_gitmap_js_form_submit`
  </td>
  <td>
    `gitmap_widget_checkbox OPT_WIDGET_MORE_SETTING lable=[System%20Param%20Setting] title=show%20widgets onclick=html_gitmap_js_form_submit`
  </td>

  <td>[ColorTheme:`html_gitmap_widget_color_theme`]</td>
  <td>    <input type="submit" name="OPT_SUBMIT" value="Refresh"> </td>
</tr>

<tr>
    <td></td>
    <td>
       <div class="widget_more$OPT_WIDGET_MORE">
        `gitmap_widget_checkbox OPT_WIDGET_NAV on lable=widget[files] title=nav onclick=html_gitmap_js_form_submit` <br/>
        `gitmap_widget_checkbox OPT_WIDGET_HISTORY on lable=widget[history] title=history onclick=html_gitmap_js_form_submit` <br/>
        `gitmap_widget_checkbox OPT_WIDGET_TIMELINE on lable=widget[timeline] title=timeline onclick=html_gitmap_js_form_submit` <br/>
        `gitmap_widget_checkbox OPT_WIDGET_BODY on lable=widget[body] title=body onclick=html_gitmap_js_form_submit` <br/>
        `gitmap_widget_checkbox OPT_WIDGET_RULES on lable=widget[rules] title=rules onclick=html_gitmap_js_form_submit`<br/>
        `gitmap_widget_checkbox OPT_WIDGET_FLASHVIEW on lable=widget[flashview] title=flash%20view onclick=html_gitmap_js_form_submit`<br/>        
        </div>    
    </td>

    <td>
       <div class="widget_more$OPT_WIDGET_MORE_SETTING">
        `gitmap_widget_textfiled OPT_GRAPH_MAX_LEVEL size=2 rlable=graph%20deep%20level onchange=html_gitmap_js_form_submit` <br/>
        `gitmap_widget_textfiled OPT_GRAPH_TEXT_MAX  size=2 rlable=node%20text%20max onchange=html_gitmap_js_form_submit` <br/>        
        `gitmap_widget_checkbox OPT_WIDGET_EXPNAD_FOLDER lable=expand%20graph%20folder onclick=html_gitmap_js_form_submit` <br/>        
        `gitmap_widget_checkbox OPT_WIDGET_SHOW_MODIFIED lable=show%20modified title=show%20modified%20in%20Rules onclick=html_gitmap_js_form_submit` <br/>        
        `gitmap_widget_checkbox OPT_WIDGET_BEAUTY_PATH lable=beauty%20path title=show%20modified%20in%20Rules onclick=html_gitmap_js_form_submit` <br/>        
        </div>    
    </td>    
    <td></td>
    <td></td>

</tr>
</table>
EOF

    html_widget_tail

}


function html_gitmap_widget_color_theme(){



    {
        cat<<EOF
gray|gray        
gray7|gray7
color|color
color7|color7
EOF
    } | gitmap_widget_select OPT_WIDGET_TIME2COLOR_THEME value=color7 title=color onchange=html_gitmap_js_form_submit
    {
        cat<<EOF
group|group
EOF
    } | gitmap_widget_select OPT_WIDGET_TIME2COLOR_METHOD value=group title=method onchange=html_gitmap_js_form_submit
    echo "</div>"


    {
        cat<<EOF
60000|1minitue
120000|2minitue
300000|5minitue
600000|10minitue
1800000|30minitue
|--
3600000|1hour
7200000|2hour
21600000|6hour
32800000|8hour
|--
86400000|1day
172800000|2day
604800000|1week
2592000000|1month
31104000000|1year
EOF
    } | gitmap_widget_select OPT_WIDGET_TIME2COLOR_TIME value=86400000 title=time onchange=html_gitmap_js_form_submit


}


function html_gitmap_widget_files(){
    [ "x$OPT_REPO" == "x" ] && return;
    
    local project=`basename $OPT_REPO`
    
    local codes='
BEGIN{
    parse_opt()
}
{
files[$2]=$2
if($1 == "#0") FOLLOW[$2 "__" $3]=1
if($1 == "#1") find[$2]=$2
if($1 == "#2") current=$2

#if($1 == "#3") git[$2]=$2

}
END{
    asort(files)
    for(i=1;i<=length(files);i++){
        f=files[i]
        c="";
        if(find[f]) c="p_find"
        if(FOLLOW[f "__" OPT_COMMIT]) c=c " " "commit_assoc"
        m["OPT_FILE"]=f
        href=link_env(m)
        title=path_format_by_setting(f);
        if(current==f){
          title="<span class=\"file_current\">&gt;</span>" title  
        } 
        printf("<p class=\"%s\"><a href=\"%s\">%s</a></p>\n",c,href,title);
    }
}'  
    html_widget_head files

    local href=`link_env OPT_REPO=$OPT_REPO OPT_FILE= OPT_COMMIT= `

    cat<<EOF
<h2>Files:<a href="$href">$project</a></h2>
EOF
    {   
        list_mm_file_with_commit | sed "s|^/||;s|^|#0 |"
        list_mm_file_by_auto | sed "s|^/||;s|^|#1 |"
        [ "x$OPT_FILE" != "x" ] && echo "$OPT_FILE"|path_encode|sed "s|^|#2 |"
#        list_mm_file_from_repo | sed "s|^|#3 |"
    } | awk  "`gitmap_lib` $codes" 


    html_widget_tail
}


function html_gitmap_widget_timeline(){

    [ "x$OPT_REPO" == "x" ] && return;
    [ "x$OPT_FILE" == "x" ] && return;
   html_widget_head timeline

   cat<<EOF
<div> 
    `gitmap_widget_checkbox OPT_WIDGET_GRAPH_CLUSTER  lable=cluster onclick=html_gitmap_js_form_submit`
    <div style="float:right">
      <h3 style="display:inline"> `basename $OPT_FILE` : Timeline</h3>   
      `gitmap_widget_button_change_value OPT_WIDGET_TIMELINE value= lable=h title=hide%20this`
    </div>  
    <div style="clear:both"/>
</div>    
EOF


   


    cat<<EOF
<div style="width:100%;overflow:auto">
<div style="width:102400px">
EOF

    local codes='
BEGIN{
    parse_opt()
    cluster=""
    if(OPT_WIDGET_GRAPH_CLUSTER == "on"){
        cluster="1"
    }
}    

/^commit/{

  commit=$2
  d=$3
  t=$4
  title=d " " t
  file=""
  getline
  if(NF==0){
    getline
  }
  file=$0

  print "<div style=\"display:inline-block\">"
  address["OPT_COMMIT"]=commit;
  address["OPT_REAL_FILE"]=path_encode(file)
  print "<a href=\"" link_env(address) "\">" 
  address_img["OPT_FUN"]="html_freemind2dot"
  address_img["OPT_COMMIT"]=commit
  address_img["OPT_GRAPH_TYPE"]="png"
  address_img["OPT_CLUSTER"]=cluster
  address_img["OPT_REAL_FILE"]=path_encode(file)
  printf("%s<br/><img src=\"%s\" width=100px height=100px title=\"%s\"/>",path_format1(file),link_env(address_img),file);
  indicator=""
  if(commit == OPT_COMMIT){
    indicator="<span class=\"commit_current\">&gt;</span>"
  }
  printf("<p>%s<small>%s</small></p>",indicator,title);
  print "</a>"

  print "</div>"


}
END{
    print "</div>"

}'
    git_log_OPT_FILE | awk  "`gitmap_lib` $codes"
    
    cat<<EOF
</div>
EOF

    html_widget_tail
   
}


function html_gitmap_widget_history(){

    [ "x$OPT_REPO" == "x" ] && return;

    
    cat<<EOF
<div class="widget widget_history">
<h3>History</h3>
EOF
    local codes='
BEGIN{
    parse_opt();
    getline;
    for(i=1;i<=NF;i++) c[$i]=$i
    getline
}    
{
    if($0 ~/^commit/){
        commit=$2
        getline;
        getline;
        d=$2
        t=$3
        content="";
        m["OPT_COMMIT"]=commit
        href=link_env(m)
        label=d " " t;
        if(commit == OPT_COMMIT){
          label= "<span class=\"commit_current\">&gt;</span>" label 
        }
        class="";
        if(c[commit]){
          class="file_assoc"
        }

        while(getline>0){
            if($0 ~/^end/){ 
                break;
            }
            if(NF>0) content=content $0
        }
        printf("<div class=\"%s\" title=\"%s\"><a href=\"%s\">%s</a><br/><p>%s</p></div>\n",class,commit,href,label,content);
    }
}    
'

    {
        [ "x$OPT_FILE" != "x" ] && git_log_OPT_FILE| awk '/^commit/{printf("%s ",$2)}'
        git_log_repo_mm_files |sed "s|^commit|\nend\ncommit|"
      echo "</pre>"        
    } |  awk  "`gitmap_lib` $codes"


    cat<<EOF
</div>
EOF

   
}

function html_gitmap_js_form_hide_body(){
    cat<<EOF
document.getElementById("OPT_WIDGET_BODY").value="";
document.getElementById("main_form").submit()
EOF
}


function html_gitmap_body(){
   [ "x$OPT_FILE" == "x" ] && return;

   export OPT_GRAPH_TYPE="svgs"
   unset IS_CGI

   html_widget_head body

   [ "x$OPT_WIDGET_GRAPH_SINGLE" != "x" ] && export OPT_GRAPH_TYPE="svg"


   cat<<EOF
<div>   
    `gitmap_widget_checkbox OPT_WIDGET_GRAPH_SINGLE  lable=single title=make%20graph%20single onclick=html_gitmap_js_form_submit`
    <div style="float:right">
      <h3 style="display:inline">`basename $OPT_FILE`: Body </h3>   
      `gitmap_widget_button_change_value OPT_WIDGET_BODY value= lable=h title=hide%20this`
    </div>  
    <div style="clear:both"/>
</div>
EOF


   html_freemind2dot

   html_widget_tail
}


#TODO
function html_gitmap_widget_rules(){
   export OPT_GRAPH_TYPE="svg"
   unset IS_CGI

   html_widget_head rules

   cat<<EOF
<div>   
    <div style="float:right">
      <h3 style="display:inline"> Rules</h3>   
      `gitmap_widget_button_change_value OPT_WIDGET_RULES value= lable=h title=hide%20this`
    </div>  
    <div style="clear:both"/>
</div>
EOF

   export OPT_GRAPH_TIMELINE=1

   echo "<div>"
   
   cat<<EOF
   <div style="overflow:auto">
EOF
   
   html_freemind2dot

   cat<<EOF
   </div>
EOF
   html_widget_tail
}


function html_gitmap_widget_flashview(){
    html_widget_head flashview

    local view_mm_href=`link_env OPT_FUN=html_gitmap_view_mm`

    local f=`echo $OPT_FILE|bin2hex`
    local f1=`echo $OPT_REAL_FILE|bin2hex`
    local mm_file_href=`link_env OPT_FUN=html_get_mm_file OPT_FILE_HEX=$f  OPT_REAL_FILE_HEX=$f1`

   cat<<EOF
<div>  
    <div style="float:right">
      <h3 style="display:inline"><a href="$view_mm_href" _target="blank">FlashView</a></h3>   
      `gitmap_widget_checkbox OPT_WIDGET_FLASH_ENABLE  lable=enable title=enable%20flash onclick=html_gitmap_js_form_submit`
      `gitmap_widget_button_change_value OPT_WIDGET_FLASHVIEW value= lable=h title=hide%20this`
    </div>  
    <div style="clear:both"/>
</div>
EOF

    if [ "x$OPT_FILE" != "x" ] && [ "x$OPT_WIDGET_FLASH_ENABLE" != "x" ];then

        local css="width:100%;height:400px"
        if [ "x$OPT_WIDGET_BODY" == "x" ];then
            css="width:100%;height:800px"
        fi

        cat<<EOF
<div>
<div id="flashcontent" style="$css">
     Flash plugin or Javascript are turned off.
     Activate both  and reload to view the mindmap
</div>
</div>

<script type="text/javascript" src="/hr/flashviewer/flashobject.js"> </script>
<script type="text/javascript">
        var fo = new FlashObject("/hr/flashviewer/visorFreemind.swf", "", "100%", "100%", 6, "#9999ff");
        fo.addParam("quality", "high");
        fo.addParam("bgcolor", "#ffffff");
        fo.addVariable("openUrl", "${mm_file_href}");
        fo.addVariable("initLoadFile", "${mm_file_href}");
        fo.addVariable("startCollapsedToLevel","5");
        fo.write("flashcontent");
</script>

EOF
     fi


    html_widget_tail
}

#function fun OPT_XXX dft_vale
function load_widget(){
 local fun=$1
 local name=$2
 local dft_value=$3

 local value;
 if env |grep "^OPT_SUBMIT=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
 else
    value=$dft_value
 fi

 if [ "x$value" == "xon" ]  || [ "x$value" == "xON" ];then
   $fun
 fi
 
}


function html_gitmap(){
    local F="html_gitmap"
    export OPT_FUN=$F

    if [ "x$1"  == "x" ] && [ "x$OPT_FILE" == "x" ] && [ "x$OPT_REPO" == "x" ] ;then 
      [ ! -d $BD ] && { echo "not found $BD";return; }
      html_gitmap_noargs
      return
    fi

     html_response_type "text/html"


    


     cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<style type="text/css">

.nav{


}

.column_left{
    float: left; 
    width: 20%;
    overflow:auto
}

.column_body{
    float: left; 
    width: 80%;
    overflow:auto
}

.tail{

}

.widget{
  border:1px solid #F0F0F0; 
}

.widget_files{
    height:60%;
    overflow:auto;
}

.widget_history{
    height:30%;
    overflow-y:auto;
}

.file_current{
  background-color:#FFFF00;
}
.file_assoc{
  background-color:#FFFF00;
}
.commit_current{
background-color:#00FFFF;
}
.commit_assoc{
  background-color:#00FFFF;
}


.widget_more{
    display:none
}

.widget_moreon{

    display:block
}

</style>
</head>
<body>
`html_gitmap_form_head`
<div class="nav">`html_gitmap_widget_nav`</div>
<div>
    <div class="column_left">
     `load_widget html_gitmap_widget_files OPT_WIDGET_NAV on`
    `load_widget html_gitmap_widget_history OPT_WIDGET_HISTORY on` 
    </div>

    <div class="column_body">
    `load_widget html_gitmap_widget_timeline OPT_WIDGET_TIMELINE on`
    `load_widget html_gitmap_widget_flashview OPT_WIDGET_FLASHVIEW on`
    `load_widget html_gitmap_body OPT_WIDGET_BODY on`
    `load_widget html_gitmap_widget_rules OPT_WIDGET_RULES on`
    </div>

    <div style="clear: both"/>
</div>
<div class="tail">
</div>
`html_gitmap_form_tail`
</body>
</html>     
EOF

}


function html_gitmap_view_mm(){
    html_response_type "text/html"

    export OPT_FUN="html_gitmap_view_mm"

    local f=`echo $OPT_FILE|bin2hex`
    local f1=`echo $OPT_REAL_FILE|bin2hex`
    local mm_file_href=`link_env OPT_FUN=html_get_mm_file OPT_FILE_HEX=$f  OPT_REAL_FILE_HEX=$f1`

    local main_href=`link_env  OPT_FUN=html_gitmap`

    #TODO chinese file not support by swf
    cat<<EOF
<html xml:lang="en" lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
   <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
   <title>bookmark.mm</title>
   <script type="text/javascript" src="/hr/flashviewer/flashobject.js"> </script>
</head>
<body>


<div>
<div>
<a href="${main_href}">...</a>
`html_gitmap_widget_timeline`
</div>
<div id="flashcontent" style="width:100%;height:100%">
     Flash plugin or Javascript are turned off.
     Activate both  and reload to view the mindmap
</div>
</div>

<script type="text/javascript">
        var fo = new FlashObject("/hr/flashviewer/visorFreemind.swf", "", "100%", "100%", 6, "#9999ff");
        fo.addParam("quality", "high");
        fo.addParam("bgcolor", "#ffffff");
        fo.addVariable("openUrl", "${mm_file_href}");
        fo.addVariable("initLoadFile", "${mm_file_href}");
        fo.addVariable("startCollapsedToLevel","5");
        fo.write("flashcontent");
</script>
</body>

</html>    

EOF
}

function html_test1(){
    html_response_type "text/html"
    {
    cat<<EOF
digraph g{
ranksep=0.2;
rankdir="LR";

c1 -> c2 -> c3 -> c4 -> c5;

{rank=same; n2 n3 c1;}


{rank=same; n21 n31 c4;}

n21->n3

}
EOF
    } |dot -Tsvg

}


function pre_process_dot(){

  fromdos | awk '
BEGIN{
  n=0;
}  
{

  if($1 == "#style_table"){
    style=$1;
  }
  lines[n++]=$0
}

END{

  if(style == "#style_table"){
    number=0;
    tn=0;
    for(i=0;i<n;i++){
      l=lines[i];
      m=split(l,a);
      if(l !~ /[#{}]/ && m >=1 && !EX[l]){
        tags[tn++]=l
        EX[l]=1
      }
    }

    print "digraph G {"

    print "node [shape=record margin=0 width=0.5 height=0.5]"
    print "nodesep=0;"
    print "ranksep=0;"

    size=4
    number=1;
    for(i=0;i<tn;i+=size){
      print "{rank=same " 
      printf("\"node_%s\" %s\n",number," [ label=\"\" style=invis width=0 height=0]");
      
      for(j=0;j<size;j++){
        print tags[i+j]
      }
      print "}"
      number++;
    }

    for(i=1;i<number-1;i++){
      printf("\"node_%s\" -> ",i)
    }
    printf("\"node_%s\" [style=invis]\n",i)

    print "}"


  }else{
    for(i=0;i<n;i++){
      print lines[i];
    }
  }

}'
  
}

function dot2dot(){
  pre_process_dot|awk '
BEGIN{
    OPT_DOT_DETAIL=ENVIRON["OPT_DOT_DETAIL"]
    
}
{
    
  if(OPT_DOT_DETAIL){
      if($0 ~ /->/){
        color=sprintf("#%06x",0xe0e0e0*rand());
        label++;
        
        if($0 ~ /\[/){
            print $0
        }else{
            printf("%s [penwidth=5 weight=1.0 fontsize=0.1 nolabel=\"%s\" color=\"%s\" fontcolor=\"%s\" ]\n",$0,label,color,color);     
        }
      }else{
        #color=sprintf("#%06x",0xe0e0e0*rand());
        #{}color="#ff0000"
        #print $0 " [nodesep=0.1 ranksep=0.1 fontcolor=\"" color "\"]" 
        print $0
      }      
  }else{
      print $0
  }

}'
}

#function html_dot2dot type:[text|png|svg|svgs]
function html_dot2dot(){
    [ "x$OPT_FILE" == "x" ] && export OPT_FILE=$1
    [ "x$OPT_GRAPH_TYPE" == "x" ] && export OPT_GRAPH_TYPE=$2

    local type=$OPT_GRAPH_TYPE

    if [ "x$type" == "xfile" ];then
        html_response_type "text/plain"
        get_mm_file 
        return
    fi
    


    if [ "x$type" == "xpng" ];then
        html_response_type "image/png"
        get_mm_file | dot2dot |dot -T$type
        return
    fi
    

    if [ "x$type" == "xsvg" ];then
        html_response_type "text/html"
        get_mm_file | dot2dot |dot -T$type
        return
    fi
    
    if [ "x$type" == "xdot" ];then
        html_response_type "text/html"
        get_mm_file | dot2dot |dot
        return
    fi    

    
    html_response_type "text/html"
    get_mm_file | dot2dot
}


OPT_LOG_FILE_DEFAULT="/var/www/html/data/loginfo/html_dot2dot.loginfo.log"

function html_gitdot(){
    local F="html_gitdot"
    export OPT_FUN=$F



    if [ "x$1"  == "x" ] && [ "x$OPT_FILE" == "x" ] && [ "x$OPT_REPO" == "x" ] ;then 
      [ ! -d $BD ] && { echo "not found $BD";return; }
      html_gitmap_noargs
      return
    fi

     html_response_type "text/html"


     [ "x$OPT_LOG_FILE" == "x" ] && OPT_LOG_FILE=$OPT_LOG_FILE_DEFAULT

     local file_option_html=`find -L /var/www/html/data/loginfo/ -name "*.loginfo.log" |awk '{printf("<option value=\"%s\">%s</option>\n",$1,gensub(".*/","","",$1))}'`

     unset IS_CGI
     export OPT_GRAPH_TYPE="svg"

     cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, user-scalable=yes"/>
<link rel="stylesheet" href="/hr/jquery-ui/jquery-ui.css">
<script src="/hr/jquery.min.js"></script>
<script src="/hr/jquery-ui/jquery-ui.js"></script>  


<script>
 
 var index=0;
 var nodes= [];
 var ids=[];
 var log_file="$OPT_LOG_FILE";
 var log_category="$OPT_REPO/$OPT_FILE"

 function send_record_log(log_file,log_category,log_tag,log_value){
          \$.ajax({
            url: "/loginfo.cgi?fun=html_log_json&OPT_LOG_FILE=" + log_file + "&OPT_LOG_TAG=" + log_tag + "&OPT_LOG_CATEGORY=" + log_category + "&OPT_LOG_VALUE=" + log_value,
            context: document.body
          }).done(function() {
          });
 }

 function reset_toolbar(){
  \$(".toolbar").hide();
  \$(".toolbar_body_toggleA").show();
}


  
 var timer=0;
 var time=0;
 var pause=false;
 function update_widget_timer(){
    var s = time % 60;
    var m = (time - s)/60%60;
    var h = (time - m*60 -s )/3600
    if(h < 10){ h = "0" + h}
    if(m < 10){ m = "0" + m}
    if(s < 10){ s = "0" + s}      
    \$(".toolbar_timer_result").html(h + ":" +m + ":" + s);
 }
 function start_timer(){
   stop_timer()
   time=0;
   pause=false;
   timer=setInterval(function(){
      update_widget_timer();
      if(!pause) time++;
    },1000);
 }

 function stop_timer(){
  clearInterval(timer);
  timer=0;
 }

 function pause_timer(){
  pause=!pause;
 }

 function close_timer(){
  stop_timer();
 }

 function do_work_model_cidian(title){
    \$("#frame_helper").attr("src", "http://dict.baidu.com/s?wd="+title+"&device=mobile");
 }

  function do_work_model_pinyin(title,node){
          \$.getJSON( "?fun=html_hanzi2pinyin_json&OPT_HANZI=" + title, function( data ) {
             var items = [];
             var hanzi;
             var pinyin;
             \$.each( data, function( key, val ) {
                if(key == "hanzi"){
                  hanzi=val;
                }
                if(key == "pinyin"){
                  pinyin=val;
                }
 
             });
             var text = \$(node).find("text").html();
             \$(node).find("text").html(pinyin);
             setTimeout(function(){
                 \$(node).find("text").html(title);
             }, 2000);
          });
}

 var layout=0;

  \$(document).ready(function(){
    \$(".node").click(function() {

       var title=\$(this).find("title").html();
       var node=this;

       var work_model=\$("#OPT_WORK_MODEL").val();
       if(work_model == "model_cidian"){
          do_work_model_cidian(title);
          return;
       }else if(work_model == "model_pinyin"){
          do_work_model_pinyin(title,this);
       }
       \$("#toolbar_title").html(title);

        //TODO
        var newColor = '#'+(0x1000000+(Math.random())*0xffffff).toString(16).substr(1,6);
        var color= \$(this).attr("color");
        var model= \$("#OPT_SELECT_MODEL").val();

        if(typeof(color) == "undefined" || color == "#ffffff"){
            newColor = "#00ff00";    
            if(model == 2){
              newColor = "#ff0000";
            }
        }else if(color == "#00ff00"){
          newColor = "#ff0000";
          if(model == 2){
            newColor = "#ffffff";
          }
        }else if(color == "#ff0000"){
          newColor = "#ffffff";
          if(model == 2){
            newColor = "#00ff00";
          }
        }else{
          newColor = "#ffffff"
        }

        var svg_item="ellipse,polygon"

        \$(this).attr("value", title)
        \$(this).attr("color", newColor)
        \$(this).find(svg_item).attr("fill", newColor).addClass("node_click")
        nodes[index]=title;
        ids[index]=\$(this).attr("id")

        if(index>=2 && nodes[index-2] == title && nodes[index-1] != title){
          var text= title + "->" + nodes[index-1]
          \$("#" + ids[index-1]).find(svg_item).attr("fill", newColor)
          \$( ".result" ).append( text + "\n");
        }
        index++;

        if(\$('#auto_check').is(':checked')){
          send_record_log(log_file,log_category,title,""); 
        }

    });  

    \$(".edge").click(function() {
         var newColor = '#'+(0x1000000+(Math.random())*0xffffff).toString(16).substr(1,6);
        \$(this).find("polygon").attr("fill", newColor)
    });  

    \$(".button_summary").click(function(){
       var total = \$(".node").size();
       var click = \$(".node_click").size();
       alert("total:" + total + " left:"+ (total-click));
    })
  

    \$(".button_save").click(function(){
       var model= \$("#OPT_SELECT_MODEL").val();
       var msg="";
       var x=window.confirm("Are you summit marks,current model("+model+")?");
       if(!x)
        return;

       \$(".node").each(function(){
          var v=\$(this).attr("value");
          var c=\$(this).attr("color");
          if(typeof(v) == "undefined"){
            v=\$(this).find("title").html();
          }
          v=v.replace(/ /,"__BLANK__")
          if(c == "#ff0000"){
             msg += v + ",0,"
          }else if(c == "#00ff00"){
             msg += v + ",10,"
          }else{
             if(model == 1){
                msg += v + ",0,"
            }else if(model == 2){
                msg += v + ",10,"
            }
          }
          if(msg.length > 1000){
            send_record_log(log_file,log_category,"SCORE_SAVE",msg);          
            msg="";
          }
       });
       if(msg.length > 0){
         send_record_log(log_file,log_category,"SCORE_SAVE",msg);          
       }
    })  

    

    \$("#OPT_LOG_FILE_SELECT").change(function(){
       var f=\$("#OPT_LOG_FILE_SELECT").val();
       if(f){
        log_file=f;
       }else{
        log_file="$OPT_LOG_FILE"
       }
    })  

    \$("#OPT_WORK_MODEL").change(function(){
       var model = \$(this).val();
       if(model == "model_cidian"){
         \$(".frame_helper_div").show();
       }else{
         \$(".frame_helper_div").hide();
       }

       if(f){
        log_file=f;
       }else{
        log_file="$OPT_LOG_FILE"
       }
    })  



    \$(".toolbar_log_record").click(function(){
       var title=\$("#toolbar_title").html();
       if(title){
        var value=\$(this).attr("value");
        if(\$("#setting_always_confirm").is(':checked')){
          var x=window.confirm("Are you sure mark " + value + "?")
          if(x){
            send_record_log(log_file,log_category,title,value); 
          }
        }else{
          send_record_log(log_file,log_category,title,value); 
        }
       }else{
        alert("click item first!");
       }
    })  


    \$(".button_toolbar").click(function(){
      \$(".toolbar").toggle();
    })  

    \$(".toolbar_keyboard_toggle").click(function(){
      \$(".toolbar_body").hide();
      \$(".toolbar_keyboard").toggle();
    })  

    \$(".toolbar_body_toggleA").click(function(){
      \$(this).hide();
      \$(".toolbar_body").toggle();
    })  
    \$(".toolbar_body_toggleB").click(function(){
      \$(".toolbar_body").hide();
      \$(".toolbar_body_toggleA").show();
    })  

    \$(".toolbar_toggle").click(function(){
      var t=\$(this).attr("target");
      \$("." + t).toggle();
    })  


    \$(".toolbar_link_file").click(function(){
      var x=window.confirm("Are you sure view " + log_file + "?")
      if(x){
        window.open("/loginfo.cgi?fun=html_log_view&OPT_LOG_FILE="+log_file,'_blank');
      }
    })  

    \$(".column").hide();
    \$(".button_play_mode").click(function(){
      var value=\$(this).attr("value");
      value = (value + 1) % 3
      \$(this).attr("value",value);
      if(value == 0){
        \$(this).html("normal");
      }else if(value==1){
        \$(this).html("found right");
      }else if(value==2){
        \$(this).html("found wrong");
      }
    
    })  

   \$(".toolbar_keyboard_hide").click(function(){
      reset_toolbar();
    })

   \$(".toolbar_timer").click(function(){
      reset_toolbar();
      \$(".toolbar_timer_pad").toggle();
    })




   \$(".toolbar_timer_pad_start").click(function(){
      start_timer();
    })

   \$(".toolbar_timer_pad_pause").click(function(){
      pause_timer();
        if(pause){
          \$(this).html("resume")
        }else{
          \$(this).html("pause")
        }
    })

   \$(".toolbar_timer_pad_stop").click(function(){
      stop_timer();
    })

   \$(".toolbar_timer_pad_close").click(function(){
      close_timer();
      \$(".toolbar_timer_pad").hide();
    })


   \$(".frame_ctl_size_toggle").click(function(){
      var small_size="100";
      var big_size="400";
      var size = \$(".frame_helper_div").width();
      var newSize;
      if(size == small_size){
        newSize=big_size;
      }else{
        newSize=small_size;
      }
      \$(".frame_helper_div").width(newSize).height(newSize);
    })

  
   \$(".frame_ctl_layout_toggle").click(function(){
      layout = (layout+1)%4;
      \$(".frame_helper_div").css('top', 'auto').css('left', 'auto').css('bottom','auto').css('right','auto');
      if(layout == 0){
          \$(".frame_helper_div").css('top','0').css('right','0');
      }else if(layout == 1){
          \$(".frame_helper_div").css('bottom','0').css('right','0');
      }else if(layout == 2){
          \$(".frame_helper_div").css('bottom','0').css('left','0');
      }else if(layout == 3){
          \$(".frame_helper_div").css('top','0').css('left','0');
      }



    })


 });

</script>
<style type="text/css">

.toolbar-header{
}


button{
}

.toolbar_body{
  display:none;
}

.column{
 
}

.toolbar_keyboard{
    display:none;  
}
.toolbar_keyboard_pad,.toolbar_timer_pad{
  display:none;
  position: fixed;
  top: 0;
  left: 0;
  z-index:11;
  -webkit-backface-visibility: hidden;  /* Chrome, Safari, Opera */
  backface-visibility: hidden;  
}
.toolbar_keyboard_hide,.toolbar_log_record{
  width:40px;
  height:40px;
}

.toolbar_keyboard_space{
  height:150px;
}

.column_more{
  display:none;
}

.frame_helper_div{
  display:none;
  position: fixed;
  top: 0;
  right: 0;
  z-index:11;
  -webkit-backface-visibility: hidden;  /* Chrome, Safari, Opera */
  backface-visibility: hidden;  
  height:480px;
  width:480px;
}


</style>
</head>
<body>

<div class="toolbar toolbar_keyboard toolbar_keyboard_pad">
  <button class="toolbar_log_record" value="0">0</button> 
  <button class="toolbar_keyboard_hide">&nbsp;</button>    
  <button class="toolbar_log_record" value="10">10</button>
  <br/>
  <button class="toolbar_log_record" value="1">1</button> 
  <button class="toolbar_log_record" value="2">2</button> 
  <button class="toolbar_log_record" value="3">3</button> 
  <br/>
  <button class="toolbar_log_record" value="4">4</button> 
  <button class="toolbar_log_record" value="5">5</button> 
  <button class="toolbar_log_record" value="6">6</button> 
  <br/>
  <button class="toolbar_log_record" value="7">7</button> 
  <button class="toolbar_log_record" value="8">8</button> 
  <button class="toolbar_log_record" value="9">9</button> 
</div>


<div class="toolbar toolbar_timer_pad">
  <button class="toolbar_timer_pad_start">start</button>
  <button class="toolbar_timer_pad_pause">pause</button>
  <button class="toolbar_timer_pad_close">close</button>
  <div>
    <span class="toolbar_timer_result">00:00:00</span> 
  </div>
</div>


<button class="toolbar toolbar_body_toggleA">&lt;</button> 
<div class="toolbar toolbar_body">
  <table>
    <tr>
      <td><button class="toolbar_body_toggleB">&lt;</button></td>      
      <td><button class="toolbar_keyboard_toggle">评分板</button></td>
      <td><button class="button_save">提交成绩</button></td>
      <td>
          模式:<select id="OPT_WORK_MODEL" style="width:100px">
            <option value="">--</option>
            <option value="model_cidian">词典模式</option>
            <option value="model_pinyin">拼音模式</option>
          </select>
      </td>
      <td><button class="toolbar_toggle" target="column_more">更多设置</button></td>

    </tr>

    <tr>
      <td>
        <div id="toolbar_title"></div>
      </td>
      <td></td>
      <td></td>
      <td></td>
      <td>
        <div class="column_more">

          记录日志:<select id="OPT_LOG_FILE_SELECT" name="OPT_LOG_FILE_SELECT" style="width:100px">
            <option value="">--</option>
            $file_option_html
          </select>
          <button class="toolbar_link_file">访问日志</button>
          <br/>

          选择模式:<select id="OPT_SELECT_MODEL" style="width:100px">
            <option value="0">普通模式</option>
            <option value="1">找对模式</option>
            <option value="2">找错模式</option>
          </select>
          <br/>

          <input id="setting_always_confirm" type="checkbox" title="always confirm" checked />提交确认  <br/>
          <input id="auto_check" type="checkbox" title="auto check" />点击自动记录          <br/>

          <button class="toolbar_timer" target="toolbar_timer_pad">时钟</button>
          <button class="button_summary">统计完成数量</button> 
          <button class="toolbar_toggle" target="graph_style">显示模式</button>
          <div class="graph_style" style="display:none">
            <a href="?fun=$OPT_FUN&OPT_REPO=$OPT_REPO&OPT_FILE=$OPT_FILE&OPT_DOT_DETAIL=1">show detail</a>
            <a href="?fun=$OPT_FUN&OPT_REPO=$OPT_REPO&OPT_FILE=$OPT_FILE">hide detail</a>
          <div>

        </div>
      </td>
    </tr>
  </table>
</div>

<div class="toolbar toolbar_keyboard toolbar_keyboard_space">
</div>

<div>
 <div style="float:left">
  `html_dot2dot`
 </div>

 <div style="float:left">
     <div class="frame_helper_div">
        <div>
          <button class="frame_ctl_size_toggle">size</button>
          <button class="frame_ctl_layout_toggle">layout</button>
        </div>

       <iframe id="frame_helper" src="" width="100%" height="100%">
       </iframe>

     </div>
 </div>

 <div style="clear: both;">
 </div>

</div>
<pre class="result"></pre>
</body>
</html>     
EOF

}


#=======sync from loginfo.cgi >>

function summary_log_file(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return


  local sort_opt=` awk '
BEGIN{
   OPT_SORT_KEY=ENVIRON["OPT_SORT_KEY"]
   OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"]

   if(!OPT_SORT_KEY || OPT_SORT_KEY == "1"){
   }else{
    opt=" -k " OPT_SORT_KEY " -n "
    if(!OPT_SORT_TYPE){
   #   OPT_SORT_TYPE = "desc"
    }
   }
   if(OPT_SORT_TYPE == "desc"){
    opt=opt " -r ";
   }
   print opt
}'`

  [ "x$OPT_SORT_KEY" == 1 ]


  cat $f| awk -F "@" '
{
  VALUE[$4]=$4
}
END{
  printf("#tag@score@total");
  asort(VALUE);
  n=length(VALUE);
  for(i=1;i<=n;i++){
    title=VALUE[i];
    if(title == "") title="empty"
    printf("@%s",title);
  }
  printf("@marks@scores");
  print "";
}'

  cat $f| awk -F "@" '

BEGIN{
  SEP=ENVIRON["SEP"]
  OPT_TIMESTAMP_MAX=ENVIRON["OPT_TIMESTAMP_MAX"];
  OPT_TIMESTAMP_MIN=ENVIRON["OPT_TIMESTAMP_MIN"];
  max = int(OPT_TIMESTAMP_MAX);
  min = int(OPT_TIMESTAMP_MIN);
} 
 function valid_mark(m){
  return m == "0" || (int(m) > 0 && int(m) <=10);
 } 


 function getA(array,idx1,idx2,  idx){
  idx = idx1 SEP idx2
  if(idx in array){
    return array[idx];
  }else{
    return 0;
  }
 }

 function setA(array,value,idx1,idx2, idx){
  idx = idx1 SEP idx2
  array[idx] = value;
 }

 function computeY(t_n,t_n_1, t){
  if(t_n_1 == 0){
    return 0;
  }else{
    t = t_n - t_n_1
  }
  if(t < 20*60){
    return 0.8
  }else if(t < 60*60){
    return 0.58
  }else if(t < 60*60*24){
    return 0.44
  }else if(t < 60*60*24*7){
    return 0.26
  }else if(t < 60*60*24*30){
    return 0.23
  }else{
    return 0.21
  }
 }

 function computeN(n,  a){
   a=0.9
   return a + (1-a) * exp(-n) * exp(1);
 }

 function getSpace(t_n,t_n_1, s,i,n){
  if(!t_n_1){
    t_n_1 = firttime
  }
  s="";
  OPT_DIV=3600*24;
  n=int((t_n - t_n_1)/OPT_DIV)
  for(i=0;i<n;i++) s=s "_";
  return s;
 }

 function computeS(s_n_1,n,m_n,t_n,t_n_1,  a,b,N){
    a=(1-computeY(t_n,t_n_1));
    N=computeN(n);
    b=a*N
    return (1-b) * s_n_1 + b * m_n;
 }

 function computeS_current(s,n,t_n, y,a){
  a=0.4
  y=computeY(systime(),t_n)
  return  (1 - (1-y)*a/(n+1))*s
 }

 function computeS_fixed(s,n){
    if(s == 0){
      if(n > 0){
        s -= n;
      }
      if(s < -10){
        s = -10;
      }
      return s;
    }else{
      return s;
    }
 }

{

  if(length(OPT_TIMESTAMP_MAX) > 0){
    if(int($1) > max){
      next;
    }
  }


  if(!firttime) firttime=$1;
  if(valid_mark($4)){
    t_n=int($1);
    m_n=int($4);
    tag=$3

    n = getA(AN,tag) + 1
   
    s_n_1 = getA(AS,tag,n-1)
    t_n_1 = getA(AT,tag,n-1)

    s_n = computeS(s_n_1,n,m_n,t_n,t_n_1)

   # print "#1","tag:" tag  " n:" n " t_n:"t_n " m_n:" m_n " s_n_1:" s_n_1 " t_n_1:"t_n_1 " a :" a " N:"N " b:"b " s_n:"s_n

    setA(AS,s_n,tag,n);
    setA(AT,t_n,tag,n);
    setA(AM,m_n,tag,n)
    setA(AN,n,tag)

  }

  if(length(OPT_TIMESTAMP_MIN) > 0){
    if(int($1) <= min){
      next;
    }
  }

  TAG_TOTAL[$3]++;
  TAG_VALUE[$4]=$4
  TAG_VALUE_TOTAL[$3 "__" $4]++;
}

END{

  asort(TAG_VALUE);
  vn=length(TAG_VALUE);
  for(i in TAG_TOTAL){
    tag=i;
    n=getA(AN,tag);
    t_n=getA(AT,tag,n);
    s=int(getA(AS,tag,n)+0.5);
    total=TAG_TOTAL[i]

    printf("%s@",i);


    s_n = computeS_current(s,n,t_n)
    s_n = int(s_n + 0.5)
    s_n = computeS_fixed(s_n,n);

    printf("%s@",s_n);
    
    #printf("%s@",s)    

    printf("%s",total)
    for(j=1;j<=vn;j++){
      printf("@%s",TAG_VALUE_TOTAL[i "__" TAG_VALUE[j]])
    }

    timeline_s=""
    timeline_m=""
    for(j=1;j<=n;j++){
      t_n=getA(AT,tag,j);
      t_n_1=getA(AT,tag,j-1);
      l=getSpace(t_n,t_n_1);
      s=getA(AS,tag,j);
      s=int(s+0.5)
      timeline_s=timeline_s sprintf("%s%s",l,s == 10 ? "A":s);

      m=getA(AM,tag,j);
      m=int(m+0.5)
      timeline_m=timeline_m sprintf("%s%s",l,m == 10 ? "A":m);

    }
    print "@" timeline_m "@" timeline_s;
  }
}
' | sort -t "@" $sort_opt 

}

function summary_log_timeline(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return

  cat $f | awk -F @ '
BEGIN{
  OPT_TIMELINE_DIV=ENVIRON["OPT_TIMELINE_DIV"]
  OPT_TIMELINE_DIV=int(OPT_TIMELINE_DIV);
  if(!OPT_TIMELINE_DIV)
    OPT_TIMELINE_DIV=600
}  
{

  p=0;
  if(length(last) > 0 && ($1 - last) > OPT_TIMELINE_DIV){
    p=1
  }

  if(p){
    print last
  }

  last=$1
 
}
END{
  if(length(last) > 0)
    print last
}'
}

function generate_dot_file(){
    cat<<EOF
#style_table
digraph G {
EOF

    summary_log_file| awk -F "@" '
BEGIN{

  OPT_FUN=ENVIRON["OPT_FUN"];
  OPT_LOG_FILE=ENVIRON["OPT_LOG_FILE"];
  OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"];
  OPT_SCORE_MAX=ENVIRON["OPT_SCORE_MAX"];
  OPT_SCORE_MIN=ENVIRON["OPT_SCORE_MIN"];
  max=int(OPT_SCORE_MAX);
  min=int(OPT_SCORE_MIN);
}
{

  d=int($2);
  if(length(OPT_SCORE_MAX) > 0){
    if(d > max){
      next;
    }
  }

  if(length(OPT_SCORE_MIN) > 0){
    if(d < min){
      next;
    }
  }
  print $1
}'

    cat<<EOF
}
EOF
}

#=======end synced from loginfo.cgi <<

function html_hanzi2pinyin_json(){
  html_response_type "text/html"

  cat<<EOF
{"status":0,"hanzi":"$OPT_HANZI","pinyin":"`echo $OPT_HANZI |  hanz2piny`"}  
EOF

}



SHAREDOT=/tmp/1.dot
function html_sharedot(){


  if [ "x$OPT_PICTURE" != "x" ];then

    html_response_type "image/png"

    {
      cat <<EOF
digraph {

  `cat /tmp/1.dot|awk '{for(i=1;i<NF;i++) printf("%s ->",$i); printf("%s\n",$i)}'`
}      
EOF
    } |dot -Tpng
    return;
  fi

  html_response_type "text/html"

     cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<script src="/hr/jquery.min.js"></script>
<style type="text/css">
.body{
  float:left;
}
</style>

<script>
 \$(document).ready(function(){
    setInterval(function(){
       location.reload();
    },3000);

  });
</script>
</head>

<body>
<div>
   <div class="frame_helper_div">
     <iframe id="frame_helper" src="?fun=html_sharedot&OPT_PICTURE=1" width="100%" height="100%">
     </iframe>

   </div>
</div>

</body>
</html>
EOF
}

function html_sharedot_lite(){
  html_response_type "text/html"

  
  cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<script src="/hr/jquery.min.js"></script>
<style type="text/css">
.body{
  float:left;
}
</style>

<script>
 \$(document).ready(function(){
    \$("#send_message").click(function(){
         var msg=\$("#msg_input").val();
         msg = msg.replace(/ /g,'@');
         msg = msg.replace(/,/g, '@');
         msg = msg.replace(/。/g, '@');
         \$.getJSON( "?fun=html_sharedot_json&OPT_MESSAGE="+msg, function( data ) {
          });
      });

  });
</script>
</head>

<body>
<input id="msg_input" type="input"><button id="send_message">send</button>
</body>
</html>  

EOF
}

function html_sharedot_json(){
  html_response_type "text/html"

  if [ "x$OPT_MESSAGE" == "x" ];then
    message_status "1" "missing params"
    return;
  fi

  echo $OPT_MESSAGE |sed "s|@| |g" >> /tmp/1.dot

  cat<<EOF
{"status":0}  
EOF

}


function get_words(){
  local lines=`awk '{l=length($0);for(i=1;i<=l;i++)  print substr($0,i,1)}'|awk '{print $1}'`

  {
    [ "x$*" != "x" ] && cat $* | awk '{print "#1",$1}'
    cat<<EOF
$lines
EOF
  } | awk '
{
 if($1=="#1"){
   d[$2]=1;
 }else{
   if(!m[$1]){
     if(!d[$1])
      print $1
   }
   m[$1]=1;

 } 
}'

}

 #======================================html index==========================================

 function index_b310aea2_10df_4296_a757_1b03636f6a45()
{
    html_response_type "text/html"


    local m=`_last_month 1`
    cat<<EOF
<html>
<ul>
<li><a href="?fun=html_gitmap">html_gitmap</a></li>
</ul>
</html>

EOF

}



cgi_index="index_b310aea2_10df_4296_a757_1b03636f6a45";
cgi_functions="
html_freemind2dot
html_hanzi2pinyin_json

html_gitmap
html_gitmap_widget_nav
html_gitmap_widget_files
html_gitmap_left_bottom
html_gitmap_widget_timeline
html_gitmap_body
html_test1
html_get_mm_file
html_gitmap_view_mm

html_gitdot
html_dot2dot

html_sharedot
html_sharedot_lite
html_sharedot_json
"


#======================================================================================
#bash process system v0.3
#
#bps_type
# bps_final           : not include others
# bps_final_exclude   : not include others and not included by others
# bps_exclude         : not included by others
#======================================================================================
for bbb in ./ /usr/bin;do
    if [ -f $bbb/bps.inc ];then
  source $bbb/bps.inc bps_final_exclude "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
  break;
    fi
done

