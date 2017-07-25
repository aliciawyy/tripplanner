using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using System.Web.Mvc.Ajax;
using BookingWebApp.Models;
namespace BookingWebApp.Controllers
{
    public class HomeController : Controller
    {
        
        public JsonResult Index()
        {
            var mvcName = typeof(Controller).Assembly.GetName();
            var isMono = Type.GetType("Mono.Runtime") != null;

            ViewData["Version"] = mvcName.Version.Major + "." + mvcName.Version.Minor;
            ViewData["Runtime"] = isMono ? "Mono" : ".NET";

			return new JsonResult()
			{
				Data = new { errMsg = "test" },
                JsonRequestBehavior = JsonRequestBehavior.AllowGet 
            };
        }

        public ContentResult RunJson(string cityName, string place)
        {
            Ultility.run_cmd("../../pybooking/gmap.py",$"{cityName} {place}");
			string text = System.IO.File.ReadAllText(@"../../output/"+$"{cityName}_{place}.json");
            dynamic data = Newtonsoft.Json.JsonConvert.DeserializeObject(text);
            var list = GetActivityFromData(data, 3);
            var jsonText = Newtonsoft.Json.JsonConvert.SerializeObject(list);
            return new ContentResult { Content = jsonText, ContentType = "application/json", ContentEncoding= System.Text.Encoding.UTF8 };
		}
        public Activity[] GetActivityFromData(dynamic data, int number)
        {
            var list = new Activity[number];
            for (int i = 0; i < number;i++)
            {
                var activity = new Activity
                {
                    Rating = data[i].rating,
                    Name = data[i].name,
                    Longitude = data[i].geometry.location.lng,
                    Latitude = data[i].geometry.location.lat,
                    ImageUrl = $"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1000&photoreference={data[i].photos[0].photo_reference}&key=AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs"
                };
                list[i] = activity;
            }
            return list;
        }
        public void ReadJsonResult()
        {
			string text = System.IO.File.ReadAllText(@"result.json");
            dynamic data = Newtonsoft.Json.JsonConvert.DeserializeObject(text);
		}
    }
}
