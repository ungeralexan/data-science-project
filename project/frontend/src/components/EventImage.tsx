import React from "react";

// Import all event images
import daadImg from "../assets/stock_images/DAAD.png";
import culturalExchangeImg from "../assets/stock_images/cultural_exchange.jpg";
import machineLearningImg from "../assets/stock_images/machine_learning.jpg";
import sportsCourseImg from "../assets/stock_images/sports_course.png";
import aiImg from "../assets/stock_images/ai.jpg";
import dataScienceImg from "../assets/stock_images/data_science.jpg";
import maxPlankImg from "../assets/stock_images/max_plank.png";
import startupImg from "../assets/stock_images/startup.png";
import applicationWorkshopImg from "../assets/stock_images/application_workshop.png";
import debateImg from "../assets/stock_images/debate.png";
import museumImg from "../assets/stock_images/museum.png";
import studentOrganisationImg from "../assets/stock_images/student_organisation.jpg";
import artWorkshopImg from "../assets/stock_images/art_workshop.jpg";
import erasmusImg from "../assets/stock_images/erasmus.png";
import networkingImg from "../assets/stock_images/networking.jpg";
import sustainabilityImg from "../assets/stock_images/sustainability.png";
import bloodDonationImg from "../assets/stock_images/blood_donation.png";
import festivalTuebingenImg from "../assets/stock_images/festival_tuebingen.jpg";
import openDayImg from "../assets/stock_images/open_day.jpg";
import theatreImg from "../assets/stock_images/theatre.jpg";
import buddyImg from "../assets/stock_images/buddy.png";
import filmScreeningImg from "../assets/stock_images/film_screening.png";
import orchestraImg from "../assets/stock_images/orchestra.png";
import tournamentImg from "../assets/stock_images/tournament.jpg";
import careerfairImg from "../assets/stock_images/careerfair.avif";
import financeEventImg from "../assets/stock_images/finance_event.png";
import orientationWeekImg from "../assets/stock_images/orientation_week.png";
import trainingImg from "../assets/stock_images/training.jpg";
import cityTourImg from "../assets/stock_images/city_tour.jpg";
import germanCourseImg from "../assets/stock_images/german_course.png";
import partyImg from "../assets/stock_images/party.png";
import volunteeringImg from "../assets/stock_images/volunteering.jpg";
import climateImg from "../assets/stock_images/climate.png";
import hikeTripImg from "../assets/stock_images/hike_trip.jpg";
import readingImg from "../assets/stock_images/reading.png";
import workshopImg from "../assets/stock_images/workshop.png";
import colloquiumImg from "../assets/stock_images/colloquium.jpg";
import infoSessionImg from "../assets/stock_images/info_session.png";
import researchFairImg from "../assets/stock_images/research_fair.jpg";
import companyTalkImg from "../assets/stock_images/company_talk.jpg";
import languageCourseImg from "../assets/stock_images/language_course.png";
import scienceImg from "../assets/stock_images/science.png";
import concertEventImg from "../assets/stock_images/concert_event.jpg";
import lectureTalkImg from "../assets/stock_images/lecture_talk.jpg";
import consultingEventImg from "../assets/stock_images/consulting event.jpg";
import libraryImg from "../assets/stock_images/library.png";
import scienceFairImg from "../assets/stock_images/science_fair.png";

/*
  This file defines the EventImage component, which displays an image for an event based on a provided image key.

  EventImage Component:
    The EventImage component takes in an imageKey, title, and optional className as props.
    It uses the imageKey to look up the corresponding image from a predefined mapping of keys to images.
    If the imageKey is not found, it defaults to a standard image.
    The component then renders an img element with the selected image source, alt text, and any provided CSS class.
*/


// Map image keys to imported images
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
  workshop: workshopImg,
  workshop_png: workshopImg,      // both keys use the same file
  colloquium: colloquiumImg,
  info_session: infoSessionImg,
  research_fair: researchFairImg,
  company_talk: companyTalkImg,
  language_course: languageCourseImg,
  science: scienceImg,
  science_png: scienceImg,        // both keys use the same file
  concert_event: concertEventImg,
  lecture_talk: lectureTalkImg,
  consulting_event: consultingEventImg,
  library: libraryImg,
  science_fair: scienceFairImg,
};

// Default image if no matching key is found
const defaultImage = dataScienceImg;

// Properties for the EventImage component. 
// It includes an optional imageKey, a title, and an optional className for styling.
interface EventImageProps {
  imageKey?: string | null;
  title: string;
  className?: string;
}

// EventImage component definition
// This component displays an event image based on the provided imageKey.
const EventImage: React.FC<EventImageProps> = ({ imageKey, title, className }) => {
  const src =
    imageKey && eventImageMap[imageKey] ? eventImageMap[imageKey] : defaultImage;

  return <img src={src} alt={title} className={className} />;
};

export default EventImage;
