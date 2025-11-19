import { useEvents } from "../hooks/useEvents";
import "./css/EventList.css"; // ⬅️ make sure the path is correct

// --- Image imports ---
import daadImg from "../assets/stock_images/DAAD.png";
import culturalExchangeImg from "../assets/stock_images/cultural_exchange.jpg";
import machineLearningImg from "../assets/stock_images/machine_learning.jpg";
import sportsCourseImg from "../assets/stock_images/sports_course.jpg";
import aiImg from "../assets/stock_images/ai.jpg";
import dataScienceImg from "../assets/stock_images/data_science.jpg";
import maxPlankImg from "../assets/stock_images/max_plank.png";
import startupImg from "../assets/stock_images/startup.jpg";
import applicationWorkshopImg from "../assets/stock_images/application_workshop.png";
import debateImg from "../assets/stock_images/debate.jpg";
import museumImg from "../assets/stock_images/museum.jpg";
import studentOrganisationImg from "../assets/stock_images/student_organisation.jpg";
import artWorkshopImg from "../assets/stock_images/art_workshop.jpg";
import erasmusImg from "../assets/stock_images/erasmus.jpg";
import networkingImg from "../assets/stock_images/networking.jpg";
import sustainabilityImg from "../assets/stock_images/sustainability.jpg";
import bloodDonationImg from "../assets/stock_images/blood_donation.png";
import festivalTuebingenImg from "../assets/stock_images/festival_tuebingen.jpg";
import openDayImg from "../assets/stock_images/open_day.jpg";
import theatreImg from "../assets/stock_images/theatre.jpg";
import buddyImg from "../assets/stock_images/buddy.jpg";
import filmScreeningImg from "../assets/stock_images/film_screening.jpg";
import orchestraImg from "../assets/stock_images/orchestra.jpg";
import tournamentImg from "../assets/stock_images/tournament.jpg";
import careerfairImg from "../assets/stock_images/careerfair.avif";
import financeEventImg from "../assets/stock_images/finance_event.jpg";
import orientationWeekImg from "../assets/stock_images/orientation_week.jpg";
import trainingImg from "../assets/stock_images/training.jpg";
import cityTourImg from "../assets/stock_images/city_tour.jpg";
import germanCourseImg from "../assets/stock_images/german_course.jpg";
import partyImg from "../assets/stock_images/party.jpg";
import volunteeringImg from "../assets/stock_images/volunteering.jpg";
import climateImg from "../assets/stock_images/climate.jpg";
import hikeTripImg from "../assets/stock_images/hike_trip.jpg";
import readingImg from "../assets/stock_images/reading.jpg";
import workshopJpgImg from "../assets/stock_images/workshop.jpg";
import workshopPngImg from "../assets/stock_images/workshop.png";
import colloquiumImg from "../assets/stock_images/colloquium.jpg";
import infoSessionImg from "../assets/stock_images/info_session.jpg";
import researchFairImg from "../assets/stock_images/research_fair.jpg";
import companyTalkImg from "../assets/stock_images/company_talk.jpg";
import languageCourseImg from "../assets/stock_images/language_course.jpg";
import scienceJpgImg from "../assets/stock_images/science.jpg";
import sciencePngImg from "../assets/stock_images/science.png";
import concertEventImg from "../assets/stock_images/concert_event.jpg";
import lectureTalkImg from "../assets/stock_images/lecture_talk.jpg";
import consultingEventImg from "../assets/stock_images/consulting event.jpg";
import libraryImg from "../assets/stock_images/library.jpg";
import scienceFairImg from "../assets/stock_images/science_fair.jpg";

// Map backend image_key -> imported image
const eventImageMap: Record<string, string> = {
  daad: daadImg,
  cultural_exchange: culturalExchangeImg,
  machine_learning: machineLearningImg,
  sports_course: sportsCourseImg,
  ai: aiImg,
  data_science: dataScienceImg,
  max_plank: maxPlankImg,
  startup: startupImg,
  application_workshop: applicationWorkshopImg,
  debate: debateImg,
  museum: museumImg,
  student_organisation: studentOrganisationImg,
  art_workshop: artWorkshopImg,
  erasmus: erasmusImg,
  networking: networkingImg,
  sustainability: sustainabilityImg,
  blood_donation: bloodDonationImg,
  festival_tuebingen: festivalTuebingenImg,
  open_day: openDayImg,
  theatre: theatreImg,
  buddy: buddyImg,
  film_screening: filmScreeningImg,
  orchestra: orchestraImg,
  tournament: tournamentImg,
  careerfair: careerfairImg,
  finance_event: financeEventImg,
  orientation_week: orientationWeekImg,
  training: trainingImg,
  city_tour: cityTourImg,
  german_course: germanCourseImg,
  party: partyImg,
  volunteering: volunteeringImg,
  climate: climateImg,
  hike_trip: hikeTripImg,
  reading: readingImg,
  workshop: workshopJpgImg,
  workshop_png: workshopPngImg,
  colloquium: colloquiumImg,
  info_session: infoSessionImg,
  research_fair: researchFairImg,
  company_talk: companyTalkImg,
  language_course: languageCourseImg,
  science: scienceJpgImg,
  science_png: sciencePngImg,
  concert_event: concertEventImg,
  lecture_talk: lectureTalkImg,
  consulting_event: consultingEventImg,
  library: libraryImg,
  science_fair: scienceFairImg,
};

const defaultImage = dataScienceImg;

export default function EventList() {
  const { events, error } = useEvents();

  if (error) {
    return <div className="event-list__error">Error: {error}</div>;
  }

  return (
    <div className="event-list">
      {events.length === 0 ? (
        <p className="event-list__empty">No events received yet.</p>
      ) : (
        <div className="event-grid">
          {events.map((event) => {
            const imageSrc =
              event.image_key && eventImageMap[event.image_key]
                ? eventImageMap[event.image_key]
                : defaultImage;

            return (
              <div key={event.id} className="event-card">
                <div className="event-card__image-placeholder">
                  <img
                    src={imageSrc}
                    alt={event.event_title}
                    className="event-card__image"
                  />
                </div>

                <div className="event-card__title">{event.event_title}</div>

                <div className="event-card__datetime">
                  {new Date(event.start_date).toLocaleString()} –{" "}
                  {new Date(event.end_date).toLocaleString()}
                </div>

                {event.location && (
                  <div className="event-card__location">{event.location}</div>
                )}

                {event.description && (
                  <div className="event-card__description">
                    {event.description}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}