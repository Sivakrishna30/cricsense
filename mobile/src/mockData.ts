import { MatchAnalysis, MatchdayResponse, PlayerHistoryRow, PlayerSummary, TeamGeneration } from './types';

export const mockMatchday: MatchdayResponse = {
  date: '2026-04-18',
  competition: 'Indian Premier League',
  matches: [
    {
      id: 'rcb-csk-demo',
      name: 'Royal Challengers Bengaluru vs Chennai Super Kings',
      status: 'Tonight, 7:30 PM',
      venue: 'M. Chinnaswamy Stadium, Bengaluru',
      teams: ['Royal Challengers Bengaluru', 'Chennai Super Kings'],
      weather: {
        city: 'Bengaluru',
        temperature_c: 28,
        precipitation_probability: 10,
        wind_speed_kmh: 12,
        summary_text: '28C, light wind, low rain chance, mild dew risk',
      },
      squad_source: 'actual',
      squads: [
        {
          teamName: 'Royal Challengers Bengaluru',
          shortname: 'RCB',
          players: [
            { name: 'Virat Kohli', role: 'Batter', country: 'India' },
            { name: 'Rajat Patidar', role: 'Batter', country: 'India' },
            { name: 'Jitesh Sharma', role: 'Wicketkeeper', country: 'India' },
            { name: 'Tim David', role: 'Batter', country: 'Australia' },
            { name: 'Krunal Pandya', role: 'Allrounder', country: 'India' },
            { name: 'Bhuvneshwar Kumar', role: 'Bowler', country: 'India' },
          ],
        },
        {
          teamName: 'Chennai Super Kings',
          shortname: 'CSK',
          players: [
            { name: 'Ruturaj Gaikwad', role: 'Batter', country: 'India' },
            { name: 'MS Dhoni', role: 'Wicketkeeper', country: 'India' },
            { name: 'Shivam Dube', role: 'Allrounder', country: 'India' },
            { name: 'Ravindra Jadeja', role: 'Allrounder', country: 'India' },
            { name: 'Matheesha Pathirana', role: 'Bowler', country: 'Sri Lanka' },
            { name: 'Khaleel Ahmed', role: 'Bowler', country: 'India' },
          ],
        },
      ],
    },
  ],
};

export const mockAnalysis: MatchAnalysis = {
  match_name: 'Royal Challengers Bengaluru vs Chennai Super Kings',
  favorite_team: 'Royal Challengers Bengaluru',
  conditions: { tags: ['batting_friendly', 'dew'] },
  players: [
    {
      player_name: 'Virat Kohli',
      team_name: 'Royal Challengers Bengaluru',
      role_profile: 'batter',
      play_type: 'top_order_anchor',
      fantasy_category: 'BAT',
      runtime_score: 88.4,
      tags: ['in_form', 'strong_vs_pace'],
      insights: ['Strong recent form in this competition', 'Good batting record at this venue'],
    },
    {
      player_name: 'Shivam Dube',
      team_name: 'Chennai Super Kings',
      role_profile: 'all_rounder',
      play_type: 'finisher',
      fantasy_category: 'AR',
      runtime_score: 84.1,
      tags: ['death_over_specialist'],
      insights: ['Useful in death-over phases', 'Dew may help chasing batters'],
    },
    {
      player_name: 'Ravindra Jadeja',
      team_name: 'Chennai Super Kings',
      role_profile: 'all_rounder',
      play_type: 'control_all_rounder',
      fantasy_category: 'AR',
      runtime_score: 80.7,
      tags: ['two_way_points'],
      insights: ['Can contribute in both disciplines'],
    },
    {
      player_name: 'Rajat Patidar',
      team_name: 'Royal Challengers Bengaluru',
      role_profile: 'batter',
      play_type: 'middle_order_batter',
      fantasy_category: 'BAT',
      runtime_score: 77.2,
      tags: ['in_form'],
      insights: ['Consistent recent returns in this competition'],
    },
    {
      player_name: 'Bhuvneshwar Kumar',
      team_name: 'Royal Challengers Bengaluru',
      role_profile: 'bowler',
      play_type: 'powerplay_bowler',
      fantasy_category: 'BWL',
      runtime_score: 73.9,
      tags: ['swing_help'],
      insights: ['Pace may get some help early'],
    },
  ],
};

export const mockTeams: TeamGeneration = {
  match_name: 'Royal Challengers Bengaluru vs Chennai Super Kings',
  favorite_team: 'Royal Challengers Bengaluru',
  disclaimer:
    'These fantasy outputs are analytical suggestions only. Feel free to use your own instinct before finalizing captain and vice-captain.',
  captain_suggestions: [
    {
      type: 'safe_pair',
      captain: 'Virat Kohli',
      vice_captain: 'Shivam Dube',
      reason: 'Best for balanced builds using top runtime and stability signals.',
    },
    {
      type: 'upside_pair',
      captain: 'Shivam Dube',
      vice_captain: 'Virat Kohli',
      reason: 'Better for higher-risk contests where upside matters more.',
    },
  ],
  common_team_1: {
    team_type: 'common_team_1',
    captain: 'Virat Kohli',
    vice_captain: 'Shivam Dube',
    players: [
      { player_name: 'Jitesh Sharma', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'WK', runtime_score: 66.2, insights: [] },
      { player_name: 'Virat Kohli', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 88.4, insights: [] },
      { player_name: 'Rajat Patidar', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 77.2, insights: [] },
      { player_name: 'Ruturaj Gaikwad', team_name: 'Chennai Super Kings', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 74.3, insights: [] },
      { player_name: 'Tim David', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 69.7, insights: [] },
      { player_name: 'Shivam Dube', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 84.1, insights: [] },
      { player_name: 'Ravindra Jadeja', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 80.7, insights: [] },
      { player_name: 'Bhuvneshwar Kumar', team_name: 'Royal Challengers Bengaluru', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 73.9, insights: [] },
      { player_name: 'Khaleel Ahmed', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 68.1, insights: [] },
      { player_name: 'Matheesha Pathirana', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 72.8, insights: [] },
      { player_name: 'Krunal Pandya', team_name: 'Royal Challengers Bengaluru', role_profile: 'all_rounder', fantasy_category: 'BWL', runtime_score: 65.4, insights: [] },
    ],
  },
  common_team_2: {
    team_type: 'common_team_2',
    captain: 'Ravindra Jadeja',
    vice_captain: 'Virat Kohli',
    players: [
      { player_name: 'MS Dhoni', team_name: 'Chennai Super Kings', role_profile: 'batter', fantasy_category: 'WK', runtime_score: 57.4, insights: [] },
      { player_name: 'Virat Kohli', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 88.4, insights: [] },
      { player_name: 'Rajat Patidar', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 77.2, insights: [] },
      { player_name: 'Ruturaj Gaikwad', team_name: 'Chennai Super Kings', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 74.3, insights: [] },
      { player_name: 'Tim David', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 69.7, insights: [] },
      { player_name: 'Ravindra Jadeja', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 80.7, insights: [] },
      { player_name: 'Shivam Dube', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 84.1, insights: [] },
      { player_name: 'Krunal Pandya', team_name: 'Royal Challengers Bengaluru', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 65.4, insights: [] },
      { player_name: 'Bhuvneshwar Kumar', team_name: 'Royal Challengers Bengaluru', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 73.9, insights: [] },
      { player_name: 'Khaleel Ahmed', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 68.1, insights: [] },
      { player_name: 'Matheesha Pathirana', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 72.8, insights: [] },
    ],
  },
  risky_team: {
    team_type: 'risky_team',
    captain: 'Shivam Dube',
    vice_captain: 'Matheesha Pathirana',
    players: [
      { player_name: 'Jitesh Sharma', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'WK', runtime_score: 66.2, insights: [] },
      { player_name: 'Tim David', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 69.7, insights: [] },
      { player_name: 'Rajat Patidar', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 77.2, insights: [] },
      { player_name: 'Ruturaj Gaikwad', team_name: 'Chennai Super Kings', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 74.3, insights: [] },
      { player_name: 'Virat Kohli', team_name: 'Royal Challengers Bengaluru', role_profile: 'batter', fantasy_category: 'BAT', runtime_score: 88.4, insights: [] },
      { player_name: 'Shivam Dube', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 84.1, insights: [] },
      { player_name: 'Ravindra Jadeja', team_name: 'Chennai Super Kings', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 80.7, insights: [] },
      { player_name: 'Krunal Pandya', team_name: 'Royal Challengers Bengaluru', role_profile: 'all_rounder', fantasy_category: 'AR', runtime_score: 65.4, insights: [] },
      { player_name: 'Bhuvneshwar Kumar', team_name: 'Royal Challengers Bengaluru', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 73.9, insights: [] },
      { player_name: 'Matheesha Pathirana', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 72.8, insights: [] },
      { player_name: 'Khaleel Ahmed', team_name: 'Chennai Super Kings', role_profile: 'bowler', fantasy_category: 'BWL', runtime_score: 68.1, insights: [] },
    ],
  },
};

export const mockPlayer: PlayerSummary = {
  player_name: 'Virat Kohli',
  role_profile: 'batter',
  play_type: 'top_order_anchor',
  base_stats_score: 86,
  context_score: 78,
  instinct_score: 66,
  final_score: 82,
  recent_form_score: 91,
  consistency_score: 89,
  strength_tags: ['In form', 'Strong at Bengaluru', 'Reliable chaser'],
  risk_tags: ['Can slow down against quality spin'],
  weakness_summary: 'Spin can reduce scoring speed when the surface grips.',
};

export const mockHistory: PlayerHistoryRow[] = [
  { match_date: '2026-04-12', event_name: 'Indian Premier League', venue: 'Bengaluru', runs: 74, balls: 46 },
  { match_date: '2026-04-08', event_name: 'Indian Premier League', venue: 'Mumbai', runs: 51, balls: 35 },
  { match_date: '2026-04-05', event_name: 'Indian Premier League', venue: 'Bengaluru', runs: 62, balls: 42 },
];
