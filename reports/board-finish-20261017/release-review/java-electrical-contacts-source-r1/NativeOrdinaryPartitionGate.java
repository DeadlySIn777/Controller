import app.freerouting.Freerouting;
import app.freerouting.settings.GlobalSettings;
import app.freerouting.board.facade.BasicBoard;
import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.board.model.items.*;
import app.freerouting.board.model.structure.FixedState;
import app.freerouting.board.state.BoardObserverAdaptor;
import app.freerouting.board.actions.ItemIdGenerator;
import app.freerouting.io.*;
import app.freerouting.io.specctra.DsnReader;
import app.freerouting.io.specctra.SesWriter;
import app.freerouting.util.gson.GsonProvider;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
/** Exactly one immutable load, two read-only query policies, no scheduler/native worker. */
public final class NativeOrdinaryPartitionGate {
 static final String PROPERTY="controller.freerouting.electricalAllContacts";
 static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
 static String sha(Path p)throws Exception{return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
 static Set<String> lines(Path p)throws Exception{var result=new TreeSet<String>();for(var s:Files.readAllLines(p))require(!s.isBlank()&&result.add(s),"blank/duplicate manifest");return result;}
 static String key(Pin p){return p.componentName()+"."+p.board.components.get(p.getComponentId()).getPackage().getPin(p.getPinIndex()).name+"#0";}
 static void save(BasicBoard board,Path p)throws Exception{try(var out=Files.newOutputStream(p,StandardOpenOption.CREATE_NEW)){SesWriter.write(board,out,"java_electrical_load_control.dsn");}require(Files.size(p)>0,"empty SES");}
 static List<List<String>> canonical(JsonArray a){var r=new ArrayList<List<String>>();for(var group:a){var g=new ArrayList<String>();for(var value:group.getAsJsonArray())g.add(value.getAsString());Collections.sort(g);r.add(g);}r.sort(Comparator.comparing(Object::toString));return r;}
 static Map<String,Object> observe(BasicBoard board,Set<String> ordinary,JsonObject expected,boolean electrical,Path output)throws Exception {
  System.setProperty(PROPERTY,Boolean.toString(electrical));var nets=new TreeMap<String,Object>();var disagreements=new ArrayList<Object>();int queries=0,pads=0,joins=0,missingPairs=0,extraPairs=0,asymmetry=0;long start=System.nanoTime();
  for(int n=1;n<=board.rules.nets.maxNetNumber();n++){
   var net=board.rules.nets.get(n);if(net==null||!ordinary.contains(net.name))continue;
   var pins=new TreeMap<String,Pin>();for(var item:board.getConnectableItems(n))if(item instanceof Pin pin)require(pins.put(key(pin),pin)==null,"duplicate ordinary pin context");
   require(expected.has(net.name),"native net missing "+net.name);var eg=canonical(expected.getAsJsonArray(net.name));var inventory=new TreeSet<String>();for(var g:eg)for(var k:g)require(inventory.add(k),"duplicate native context");require(inventory.equals(pins.keySet()),"native/loaded pin inventory "+net.name);
   var oracle=new TreeMap<String,Set<String>>();for(var row:pins.entrySet()){
    var connected=new TreeSet<String>();for(var item:row.getValue().getConnectedSet(n))if(item instanceof Pin p)require(connected.add(key(p)),"query duplicate pin");
    require(connected.contains(row.getKey())&&pins.keySet().containsAll(connected),"query crossed source net/context");oracle.put(row.getKey(),connected);queries++;
   }
   var unique=new TreeMap<String,List<String>>();for(var group:oracle.values())unique.put(group.toString(),new ArrayList<>(group));var groups=new ArrayList<>(unique.values());groups.sort(Comparator.comparing(Object::toString));
   int hereAsym=0;for(var row:oracle.entrySet())for(var other:row.getValue())if(!oracle.get(other).equals(row.getValue()))hereAsym++;
   int lost=0,gained=0;var nativeByPin=new TreeMap<String,Set<String>>();for(var g:eg)for(var pin:g)nativeByPin.put(pin,new TreeSet<>(g));
   for(var row:oracle.entrySet())for(var other:pins.keySet())if(row.getKey().compareTo(other)<0){boolean before=nativeByPin.get(row.getKey()).contains(other),after=row.getValue().contains(other);if(before&&!after)lost++;if(!before&&after)gained++;}
   if(!groups.equals(eg)||hereAsym>0)disagreements.add(Map.of("net",net.name,"native_groups",eg,"observed_groups",groups,"asymmetric_query_memberships",hereAsym,"native_pairs_missing",lost,"extra_pairs",gained));
   nets.put(net.name,groups);pads+=pins.size();joins+=Math.max(0,groups.size()-1);missingPairs+=lost;extraPairs+=gained;asymmetry+=hereAsym;
   if(nets.size()%100==0)System.out.println((electrical?"ELECTRICAL":"ORIGINAL")+" nets="+nets.size()+" pins="+pads+" seconds="+(System.nanoTime()-start)/1e9);
  }
  require(nets.keySet().equals(ordinary),"not every ordinary net queried");var r=new LinkedHashMap<String,Object>();r.put("nets",nets);r.put("ordinary_net_count",nets.size());r.put("pad_contexts",pads);r.put("direct_pin_query_calls",queries);r.put("ordinary_pad_island_joins",joins);r.put("native_disagreement_nets",disagreements);r.put("native_pairs_missing",missingPairs);r.put("extra_pairs",extraPairs);r.put("asymmetric_query_memberships",asymmetry);r.put("seconds",(System.nanoTime()-start)/1e9);r.put("query",electrical?"Item.getConnectedSet allContacts opt-in":"ORIGINAL Item.getConnectedSet normalContacts default-off");
  Files.writeString(output,GsonProvider.GSON.toJson(r)+"\n",StandardOpenOption.CREATE_NEW);return r;
 }
 public static void main(String[]args)throws Exception{
  require(args.length==5,"dsn protected ordinary expectedNative output");Path dsn=Path.of(args[0]),out=Path.of(args[4]);Files.createDirectories(out);String source=sha(dsn);var protectedNets=lines(Path.of(args[1]));var ordinary=lines(Path.of(args[2]));require(Collections.disjoint(protectedNets,ordinary),"mixed scopes");var expected=JsonParser.parseString(Files.readString(Path.of(args[3]))).getAsJsonObject();require(expected.get("ordinary_net_count").getAsInt()==2153&&expected.get("pad_contexts").getAsInt()==5116&&expected.get("ordinary_pad_island_joins").getAsInt()==837,"wrong actual native authority");
  require(!Boolean.getBoolean("freerouting.stats.immutableRoutingOwner"),"statistics memo must be disabled");System.clearProperty(PROPERTY);
  Freerouting.globalSettings=new GlobalSettings();var g=Freerouting.globalSettings;g.guiSettings.isEnabled=false;g.apiServerSettings.isEnabled=false;g.mcpServerSettings.isEnabled=false;g.mcpServerSettings.isStdioMode=false;g.featureFlags.multiThreading=false;g.usageAndDiagnosticData.disableAnalytics=true;
  long start=System.nanoTime();BoardReadResult read;try(var in=Files.newInputStream(dsn)){read=DsnReader.readBoard(in,new BoardObserverAdaptor(),new ItemIdGenerator());}require(read instanceof BoardReadResult.Success,"load failed");var ok=(BoardReadResult.Success)read;require(ok.warnings().isEmpty(),"original parser warnings: "+ok.warnings());var board=(RoutingBoard)ok.board();double loadSeconds=(System.nanoTime()-start)/1e9;System.out.println("LOADED seconds="+loadSeconds);
  var allNets=new TreeSet<>(ordinary);allNets.addAll(protectedNets);var actualNets=new TreeSet<String>();for(int n=1;n<=board.rules.nets.maxNetNumber();n++){var net=board.rules.nets.get(n);if(net!=null)actualNets.add(net.name);}require(actualNets.equals(allNets)&&protectedNets.size()==235,"net/policy scope");
  board.changeConductionIsObstacle(true);
  int vias=0,pins=0,areas=0;var state=new TreeMap<Integer,String>();var fixed=new TreeMap<String,Integer>();
  for(var item:board.getItems()){
   require(state.put(item.getId(),item.getClass().getName()+"/"+item.getFixedState()+"/"+Arrays.toString(item.netNumbers))==null,"duplicate item ID");
   if(item instanceof Trace||item instanceof Via){require(item.getFixedState()==FixedState.USER_FIXED,"load-only routes not USER_FIXED");fixed.merge(item.getClass().getSimpleName()+"/"+item.getFixedState(),1,Integer::sum);}if(item instanceof Via)vias++;if(item instanceof Pin)pins++;
   if(item instanceof ConductionArea){areas++;require(item.netCount()==1&&protectedNets.contains(board.rules.nets.get(item.getNetNumber(0)).name)&&item.getFixedState()==FixedState.SYSTEM_FIXED,"cached metal not fixed protected net");}
  }
  require(vias==8017&&pins==9640&&areas==2,"source via/pin/typed-area count");int revision=board.getRevision();
  save(board,out.resolve("before-query-original.ses"));String before=sha(out.resolve("before-query-original.ses"));
  var original=observe(board,ordinary,expected.getAsJsonObject("nets"),false,out.resolve("original-normal-contact-partitions.json"));
  var electrical=observe(board,ordinary,expected.getAsJsonObject("nets"),true,out.resolve("optin-electrical-partitions.json"));System.clearProperty(PROPERTY);
  var finalState=new TreeMap<Integer,String>();for(var item:board.getItems())finalState.put(item.getId(),item.getClass().getName()+"/"+item.getFixedState()+"/"+Arrays.toString(item.netNumbers));require(state.equals(finalState)&&revision==board.getRevision(),"query modified item/net/fixed/revision");save(board,out.resolve("after-query-original.ses"));require(before.equals(sha(out.resolve("after-query-original.ses")))&&source.equals(sha(dsn)),"physical projection/input changed");
  boolean pass=((Number)electrical.get("pad_contexts")).intValue()==5116&&((Number)electrical.get("ordinary_pad_island_joins")).intValue()==837&&((List<?>)electrical.get("native_disagreement_nets")).isEmpty()&&((Number)electrical.get("asymmetric_query_memberships")).intValue()==0;
  var result=new LinkedHashMap<String,Object>();result.put("status",pass?"PASS_ACTUAL_JAVA_ELECTRICAL_QUERY_NATIVE_5116_837_LOAD_ONLY":"HELD_ACTUAL_JAVA_NATIVE_QUERY_DISAGREEMENT");result.put("DSN_SHA256",source);result.put("load_seconds",loadSeconds);result.put("source_vias",vias);result.put("source_pins",pins);result.put("typed_cached_protected_areas",areas);result.put("protected_nets",protectedNets.size());result.put("ordinary_nets",ordinary.size());result.put("all_loaded_route_objects_remain_USER_FIXED",true);result.put("fixed_state_counts",fixed);result.put("original_normal_contact_joins",original.get("ordinary_pad_island_joins"));result.put("original_missing_native_pairs",original.get("native_pairs_missing"));result.put("original_disagreement_nets",((List<?>)original.get("native_disagreement_nets")).size());result.put("electrical_joins",electrical.get("ordinary_pad_island_joins"));result.put("electrical_missing_native_pairs",electrical.get("native_pairs_missing"));result.put("electrical_extra_native_pairs",electrical.get("extra_pairs"));result.put("electrical_direct_pin_queries",electrical.get("direct_pin_query_calls"));result.put("all_source_SES_physical_projection_bytes_exact",true);result.put("source_SES_SHA256",before);result.put("all_item_IDs_net_fields_fixed_states_revision_exact",true);result.put("statistics_memo_enabled",false);result.put("scheduler_started",false);result.put("router_runs",0);result.put("native_workers",0);result.put("adopted",false);result.put("new_routing_cleanup_safe","NOT_QUALIFIED_BY_LOAD_ONLY");Files.writeString(out.resolve("acceptance.json"),GsonProvider.GSON.toJson(result)+"\n",StandardOpenOption.CREATE_NEW);System.out.println(GsonProvider.GSON.toJson(result));require(pass,"actual native source query gate failed");
 }
}
