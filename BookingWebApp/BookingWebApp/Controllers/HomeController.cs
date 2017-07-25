using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Web;
using System.Web.Mvc;
using System.Web.Mvc.Ajax;
using BookingWebApp.Models;
using Microsoft.VisualBasic.FileIO;

namespace BookingWebApp.Controllers
{

    public class HomeController : Controller
    {
        public ActionResult Test()
        {
            return Content(System.IO.File.ReadAllText(@"../../googlemapsample/tripplanner.html"));
        }
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
			Ultility.RunCMD("../../pybooking/gmap.py", $"{cityName} {place}");
			string text = System.IO.File.ReadAllText(@"../../output/"+$"{cityName}_{place}.json");
            dynamic data = Newtonsoft.Json.JsonConvert.DeserializeObject(text);
            var list = GetActivityFromData(data, 3);
            var jsonText = Newtonsoft.Json.JsonConvert.SerializeObject(list);
            return new ContentResult { Content = jsonText, ContentType = "application/json", ContentEncoding= System.Text.Encoding.UTF8 };
		}
		[AllowCrossSiteJson]
		public ContentResult GetPlaces(string cityName, string place)
		{
			var places = GetActivitiesCSV(cityName, place, 20);
			return Ultility.GetJsonContent(places);
		}
		[AllowCrossSiteJson]
		public ContentResult GetPlans(string cityName, string places, int duration)
		{
            //currently hard coded.
            var plan = GetPlan(cityName, places.Split(','), duration);
            return Ultility.GetJsonContent(plan);
		}

        public Activity[] GetActivities(string cityName, string place, int number)
        {
            if (string.IsNullOrEmpty(cityName) || string.IsNullOrEmpty((place))) return null;
            if (!System.IO.File.Exists(@"../../output/" + $"{cityName}_{place}.json"))
            {
                Ultility.RunCMD("../../pybooking/gmap.py", $"{cityName} {place}");
			}
			string text = System.IO.File.ReadAllText(@"../../output/" + $"{cityName}_{place}.json");

			dynamic data = Newtonsoft.Json.JsonConvert.DeserializeObject(text);
			var list = GetActivityFromData(data, number);
            return list;
		}

		public Activity[] GetActivitiesCSV(string cityName, string place, int number)
		{
			if (string.IsNullOrEmpty(cityName) || string.IsNullOrEmpty((place))) return null;
            if (!System.IO.File.Exists(@"../../output/" + $"{cityName}_{place}.csv"))
			{
				Ultility.RunCMD("../../pybooking/gmap.py", $"{cityName} {place}");
			}

			var list = GetActivityFromCSV(@"../../output/" + $"{cityName}_{place}.csv", number);
			return list;
		}

        public Day[] GetPlan(string cityName, string[] place, int duration)
        {
            const int interestPerDay = 3;
            var activities = GetActivitiesCSV(cityName, place[0], duration * interestPerDay);
            var plan = new Day[duration];
            for (int i = 0; i < duration; i++)
            {
                var day = new Day();
                day.NumberOfActivity = interestPerDay;
                day.Activities = activities.Skip(i * interestPerDay).Take(interestPerDay).ToList();
                plan[i] = day;
            }
            return plan;
        }


        public Activity[] GetActivityFromCSV(string path, int number)
        {
			var list = new Activity[number];

			using (Microsoft.VisualBasic.FileIO.TextFieldParser parser = new TextFieldParser(path,Encoding.UTF8))
			{
				parser.TextFieldType = FieldType.Delimited;
				parser.SetDelimiters(",");
                parser.ReadFields();
				//name  rating  photo_ref   place_types y   x   id
				for (int i = 0; (i < number && !parser.EndOfData); i++)
				{
					string[] fields = parser.ReadFields();

					var activity = new Activity
					{
						Name = fields[0],
						Rating = double.Parse(fields[1]),
						ImageUrl = $"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1000&photoreference={fields[2]}&key=AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs",
						Longitude = fields[4],
                        Latitude = fields[5],
                        Type = fields[3],
                        Id = fields[6]
					};
					list[i] = activity;
				}
			}
            return list;
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
