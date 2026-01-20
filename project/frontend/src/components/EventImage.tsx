import React from "react";

// Load every stock image so we can resolve png/jpg/avif variants regardless of the file extension.
const imageModules = import.meta.glob(
	"../assets/stock_images/*.{png,jpg,jpeg,avif,webp}",
	{ eager: true, as: "url" }
) as Record<string, string>;

const availableImages: Record<string, string> = Object.entries(imageModules).reduce(
	(lookup, [path, url]) => {
		const fileName = path.split("/").pop();
		if (!fileName) return lookup;
		const baseName = fileName.replace(/\.[^/.]+$/, "");
		return { ...lookup, [baseName]: url };
	},
	{}
);

// Map each event key to the matching filename (without extension).
const eventImageMap: Record<string, string> = {
	ai: "ai",
	art_workshop: "art_workshop",
	blood_donation: "blood_donation",
	buddy: "buddy",
	careerfair: "careerfair",
	city_tour: "city_tour",
	climate: "climate",
	colloquium: "colloquium",
	concert_event: "concert_event",
	company_talk: "company_talk",
	consulting_event: "consulting event",
	cultural_exchange: "cultural_exchange",
	daad: "daad",
	data_science: "data_science",
	debate: "debate",
	erasmus: "erasmus",
	festival: "festival",
	festival_tuebingen: "festival_tuebingen",
	finance_event: "finance_event",
	film_screening: "film_screening",
  graduation: "graduation",
	german_course: "german_course",
	hike_trip: "hike_trip",
	info_session: "info_session",
	language_course: "language_course",
	lecture_talk: "lecture_talk",
	library: "library",
	machine_learning: "machine_learning",
	max_plank: "max_plank",
	museum: "museum",
	networking: "networking",
	open_day: "open_day",
	orientation_week: "orientation_week",
	orchestra: "orchestra",
	party: "party",
  resume_workshop: "resume_workshop",
	reading: "reading",
	remembrance: "remembrance",
	research_fair: "research_fair",
	science: "science",
	scholarship: "scholarship",
	sports_course: "sports_course",
	startup: "startup",
	student_organization: "student_organization",
	sustainability: "sustainability",
	theatre: "theatre",
	training: "training",
	tournament: "tournament",
	volunteering: "volunteering",
	workshop: "workshop",
	workshop_png: "workshop",
	hackathon: "hackathon",
	exam_prep: "exam_prep",
	mental_health: "mental_health",
	study_skills: "study_skills",
	writing_workshop: "writing_workshop",
	thesis_info: "thesis_info",
	research_methods: "research_methods",
	panel_discussion: "panel_discussion",
	alumni_event: "alumni_event",
	meetup: "meetup",
};

const defaultImage =
	availableImages[eventImageMap["data_science"] ?? ""] ??
	Object.values(availableImages)[0] ??
	"";

interface EventImageProps {
	imageKey?: string | null;
	title: string;
	className?: string;
}

const resolveImageUrl = (imageKey?: string | null): string => {
	if (!imageKey) return defaultImage;
	const fileName = eventImageMap[imageKey];
	if (!fileName) return defaultImage;
	return availableImages[fileName] ?? defaultImage;
};

const EventImage: React.FC<EventImageProps> = ({ imageKey, title, className }) => {
	const src = resolveImageUrl(imageKey);
	return <img src={src} alt={title} className={className} />;
};

export default EventImage;

