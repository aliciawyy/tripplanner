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
            var list = GetActivityFromDynamicObject(data, 3);
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
            var activity = GetPlanActivity(cityName, places, duration);
            var plan = GetDaysFromActivities(activity);
            return Ultility.GetJsonContent(plan);
		}

        public Activity[] GetPlanActivity(string cityName, string place, int number)
        {
            var placeFileName = place.Replace(',', '-');
			//python pybooking/distance_mat.py Paris outdoor_activity,museum
            if (!System.IO.File.Exists(@"../../output/" + $"plan-{cityName}_{placeFileName}-{number}.csv"))
			{
                Ultility.RunCMD("../../pybooking/distance_mat.py", $"{cityName} {place} {number}");
			}

            var list = GetActivityFromCSV(@"../../output/" + $"plan-{cityName}_{placeFileName}-{number}.csv", 0).ToArray();
			return list;
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
			var list = GetActivityFromDynamicObject(data, number);
            return list;
		}

		public Activity[] GetActivitiesCSV(string cityName, string place, int number)
		{
			if (string.IsNullOrEmpty(cityName) || string.IsNullOrEmpty((place))) return null;
            if (!System.IO.File.Exists(@"../../output/" + $"{cityName}_{place}.csv"))
			{
				Ultility.RunCMD("../../pybooking/gmap.py", $"{cityName} {place}");
			}

            var list = GetActivityFromCSV(@"../../output/" + $"{cityName}_{place}.csv", number).ToArray();
			return list;
		}

        public List<Day> GetDaysFromActivities(Activity[] activities)
        {
            int day = 0;
            var plan = new List<Day>();
            while (activities.Any(d => d.Day == day)){
                var dayPlan = new Day();
                dayPlan.Activities = activities.Where(d => d.Day == day).ToList();
                dayPlan.NumberOfActivity = dayPlan.Activities.Count;
                plan.Add(dayPlan);
                day++;
            }
            return plan;
        }


        public List<Activity> GetActivityFromCSV(string path, int number)
        {
			var list = new List<Activity>();
            if (number == 0) number = 1000;
			using (Microsoft.VisualBasic.FileIO.TextFieldParser parser = new TextFieldParser(path,Encoding.UTF8))
			{
				parser.TextFieldType = FieldType.Delimited;
				parser.SetDelimiters(",");
                var headers = parser.ReadFields();
                int interestColumn=-1, nameColumn=0, ratingColumn=0, photoColumn=0, typeColumn=0, xColumn=0, yColumn=0, idColumn=0, dayColumn=-1;
                for (int i = 0; i < headers.Count(); i++){
                    switch(headers[i]){
                        case "interest": interestColumn = i;break;
                        case "name": nameColumn = i;break;
                        case "rating": ratingColumn = i;break;
                        case "photo_ref": photoColumn = i;break;
                        case "y": yColumn = i;break;
                        case "x":xColumn = i;break;
                        case "id":idColumn = i;break;
                        case "day_plan":dayColumn = i;break;
                        case "place_types": if (interestColumn < 0) interestColumn = i;break;
                    }                   
                }
				//interest,name,rating,photo_ref,place_types,y,x,id,transit_time,day_plan

				//name  rating  photo_ref   place_types y   x   id

				for (int i = 0; (i < number && !parser.EndOfData && i<number); i++)
				{
					string[] fields = parser.ReadFields();

                    var activity = new Activity
                    {
                        Name = fields[nameColumn],
                        Rating = double.Parse(fields[ratingColumn]),
                        ImageUrl = $"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1000&photoreference={fields[photoColumn]}&key=AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs",
                        Longitude = fields[yColumn],
                        Latitude = fields[xColumn],
                        Type = fields[interestColumn],
                        Id = fields[idColumn]
					};
                    if (dayColumn >0)
                        activity.Day = int.Parse(fields[dayColumn]);
                    list.Add(activity);
				}
			}
            return list;
        }
        public Activity[] GetActivityFromDynamicObject(dynamic data, int number)
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
