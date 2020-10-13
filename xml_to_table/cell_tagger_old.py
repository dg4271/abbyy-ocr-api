# -*- coding: utf-8 -*- 

import re


pre_symbol = "(([ \\\\«~#\^|????/*;,'??\-_1di-km)]+[hJMX \^]*|GFR)*)"
n_type = "([<>+\-±?��?]|min|max|SD|(\);|Interaction)? ?\(?[pP]( value)? ?[??<>]+|([nr]|rho)[ ??<>]+|up to|-50[GT]{,2} = )?"
number = " ?(T:|pH|[ $]*)? ?([0-9.'??^]+ ?[xX*]? ?(10|[Ee])-?[0-9]*|([0-9lo]|Q-|i[.0-9]|(\.|- ?)[0-9])[ 0-9flOQS.,'??\-\^]+|\.?[0-9])[*]*"
unit1 = "°C|%|I ?U(/d)?.*|(mg|mcg|MCU)/[dL]|[mp]?g|[mnp]mol/L|mL/min|kcal/mL|k([jl]|cal)?"
unit2 = "[(]IgG[12][)]|RAE|HD( and PD)?|PD|py|servings/(week|day).*|days?|[yY]ears|-?months?"
unit3 = "sibling/related|unrelated|light|moderate|bar|min|h( oral)?"
sex = "(% )?\(?(wo)?men\)?|(fe)?male|[(][MF][)]"
etc_unit = "% CM|m?g/dia( TTS)?|mg i\.m\.|/?semanas?|kg( peso)?|% f (fuerza|area|volumen) [a-z0-9 ]+|with( and|out body mass reduction)"
value_pattern = "{}{}({}|{}|{}|{}|{})?".format(n_type, number, unit1, unit2, unit3, sex, etc_unit)

post_symbol = "(([?�■;\^*%#&$§_<?�’”�?"',. ()\]|\\\\]|[+A-CPTXZa-flmnstwxy])*|[(][a-zR. \-]+[)])"
p1 = "[(]?%s[)]?" %(value_pattern)
p2 = "[C{(\[]? ?%s ?(to|[ ±??-,/;]) ?%s[)\]]?" %(value_pattern, value_pattern)
p3 = "%s ?_?[C({\[]([a-z ]+|%s)[_)\]]" %(value_pattern, value_pattern)
p4 = "%s[ ,/;\-]?%s ?[C({\[]([a-z ]+|%s)[)\]]" %(value_pattern, value_pattern, value_pattern)
p5 = "%s[ ]?%s" %(value_pattern, p2)
p6 = "(%s ?){2}" %(p2)
p7 = "%s([ ,/;\-]?[(\[]?%s[)\]]? ?){2}" %(value_pattern, value_pattern)
p8 = "%s; %s" %(p5, value_pattern)
p9 = "(([FM]|(M|Wom)en):? ?%s ?){2}" %(p2)
all_pattern = "^%s(%s|%s|%s|%s|%s|%s|%s|%s|%s)%s$" %(pre_symbol, p1, p2, p3, p4, p5, p6, p7, p8, p9, post_symbol)

def is_value(t):
    if t.lower() == "ns":
        return "v" 

    t = t.replace("mm°l/L", "mmol/L")

    t = t.replace("<br>", ' ')

    if re.search(all_pattern, t):

        comma_splited = t.split(',')

        if len(comma_splited) > 2 and len(comma_splited[1]) < 3:

            return "stub"

        return "v"
    
    elif t =="":
      return "empty"
    
    return "stub"


reg_distribution = [
    "[-+]?[0-9]*\.?[0-9]+ ?± ?[-+]?[0-9]*\.?[0-9]+",
    "[-+]?[0-9]*\.?[0-9]+[ ]?\([-+]?[0-9]*\.?[0-9]+\)"
]
#23.2 (21.3, 25.5)
#23.2 (21.3, 25.5)
reg_range = [
    
]
reg_values = [
    "[-+]? ?[0-9]+(\.[0-9]+)?",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?± ?[-+]?[0-9]*(\.[0-9]+)?",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?\([-+]? ?[0-9]*(\.?[0-9]+)?\)",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?\([0-9]*(\.?[0-9]+)?\)",
    "[-+]? ?[0-9]+(\.[0-9]+)?,? ?[0-9]+(\.[0-9]+)?%",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?\([0-9]+(\.[0-9]+)?,? ?-? ?[0-9]+(\.[0-9]+)?\)",
    "(< ?)?[0-9]?(\.[0-9]+)",
    "[0-9]{1,3}(,[0-9]{3})+",
    "[0-9]+(\.[0-9]+)? ?- ?[0-9]+(\.[0-9]+)?"
]
reg_value_w_pvalues = [
    "[-+]? ?[0-9]+(\.[0-9]+)? ?[*a#ptP§]{1,3}",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?± ?[-+]?[0-9]*(\.[0-9]+)? ?[*a#ptP§]{1,3}",
    "[-+]? ?[0-9]+(\.[0-9]+)? ?\([-+]?[0-9]*(\.?[0-9]+)?\) ?[*a#ptP§]{1,3}"
    "[-+]? ?[0-9]*\.?[0-9]+[*a#ptP§]{1,3} ?[*a#ptP§]{1,3}",
    "[-+]?[0-9]*\.?[0-9]+ ?± ?[-+]?[0-9]*\.?[0-9]+[*a#ptP§]{1,3}",
    "[-+]?[0-9]*\.?[0-9]+[ ]?\([-+]?[0-9]*\.?[0-9]+\)[*a#ptP§]{1,3}"
]
reg_pvalues = [
    "NS",
    "ns",
    "<0\.[0-9]+",
    "\.[0-9]+"
]

def cell_tagging(value):
    
    value = value.replace("<br>", " ")
    
    tag = "stub"
    #if value == '':
    #    tag = None
    #value = re.sub("\(.+?\)","", value)
    
    if value.startswith("<srow>"):
        return "srow"
    
    if value.startswith("<ssrow>"):
        return "ssrow"
    
    if value.startswith("<indent>"):
        return "indent"
    
    if value == "" or value == '-':
        return "empty"
    
    for reg in reg_values:
        if bool(re.fullmatch(reg, value)):
            tag = "v"
        
    for reg in reg_value_w_pvalues:
        if bool(re.fullmatch(reg, value)):
            tag = "vp"
    
    for reg in reg_pvalues:
        if bool(re.fullmatch(reg, value)):
            tag = "v"
            
    return tag
